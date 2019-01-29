import json
import uuid

from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.views.generic.base import View
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.http import urlunquote
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _

from courseware.courses import get_course_by_id
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError
from xmodule.course_module import INVOLVEMENT_OPTIONAL, INVOLVEMENT_REQUIRED

from .models import UserCourseInvolvement, UserVisitInvolvementLink, InvolvementLink
from .utils import involvement_is_enabled, ask_enable_involvement, get_user_involvement, prepare_jwt_token


class InvolvementView(View):

    @method_decorator(login_required)
    @method_decorator(transaction.atomic)
    def get(self, request, course_id):
        redirect_to = request.GET.get('next', None)
        course_key = CourseKey.from_string(course_id)
        course = get_course_by_id(course_key)
        course_outline_url = reverse('openedx.course_experience.course_home', kwargs={
            'course_id': unicode(course.id),
        })

        if ask_enable_involvement(course, request.user):
            if course.involvement == INVOLVEMENT_REQUIRED:
                msg = _("To complete the current course you must enable involvement (the camera will be turned on)")
                can_skip = False
            else:
                msg = _("At the current course you may enable involvement functions (the camera will be turned on)."
                        " This helps us to make the courses better.")
                can_skip = True
            context = {
                "can_skip": can_skip,
                "involvement_msg": msg,
                "redirect_url": redirect_to if redirect_to else '',
                "course_outline_url": course_outline_url
            }
            return render_to_response('ask_enable_involvement.html', context)
        else:
            if not redirect_to:
                redirect_to = course_outline_url
            else:
                redirect_to = urlunquote(redirect_to)
            return redirect(redirect_to)

    @method_decorator(login_required)
    @method_decorator(transaction.atomic)
    def post(self, request, course_id):
        course_key = CourseKey.from_string(course_id)
        course = get_course_by_id(course_key)

        if involvement_is_enabled(course):
            try:
                received_json_data = json.loads(request.body)
            except ValueError:
                received_json_data = {}

            try:
                involvement = UserCourseInvolvement.objects.get(course_key=course_key, user=request.user)
            except UserCourseInvolvement.DoesNotExist:
                involvement = UserCourseInvolvement(course_key=course_key, user=request.user)

            action = received_json_data.get('action')
            if action == 'allow' or (action == 'skip' and course.involvement == INVOLVEMENT_OPTIONAL):
                involvement.last_action_time = timezone.now()
                involvement.is_active = action == 'allow'
                involvement.save()
                return JsonResponse({'success': True, 'continue': True})
            elif action == 'skip' and course.involvement == INVOLVEMENT_REQUIRED:
                if involvement:
                    involvement.delete()
                return JsonResponse({'success': True, 'continue': True})
            else:
                return JsonResponse({'success': False, 'continue': False})
        else:
            return JsonResponse({'success': False, 'continue': True})


@login_required
@require_http_methods(["POST"])
def get_involvement_token(request, course_id):
    try:
        received_json_data = json.loads(request.body)
    except ValueError:
        received_json_data = {}

    usage_id = received_json_data.get('blockId', None)
    if not usage_id:
        return HttpResponseBadRequest("block-id was not passed")

    try:
        usage_key = UsageKey.from_string(usage_id)
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return HttpResponseBadRequest("Invalid parameters")

    course = get_course_by_id(course_key)
    if not involvement_is_enabled(course):
        return JsonResponse({
            'involvement_enabled': False,
            'involvement_allowed': None,
            'token': None
        })

    involvement, involvement_allowed = get_user_involvement(course_key, request.user)
    if involvement_allowed:
        link = InvolvementLink.objects.filter(course_key=course_key, usage_key=usage_key, user=request.user).first()
        if not link:
            link_id = str(uuid.uuid4())
            link = InvolvementLink.objects.create(
                link_id=link_id,
                course_key=course_id,
                usage_key=usage_key,
                block_type=usage_key.block_type,
                user=request.user
            )
        visit_id = str(uuid.uuid4())
        UserVisitInvolvementLink.objects.create(
            link=link,
            visit_time=timezone.now(),
            visit_id=visit_id
        )

        jwt_token = prepare_jwt_token({
            'access': 'w',
            'link_id': link.link_id,
            'visit_id': visit_id
        })

        return JsonResponse({
            'involvement_enabled': True,
            'involvement_allowed': True,
            'token': jwt_token
        })

    return JsonResponse({
        'involvement_enabled': True,
        'involvement_allowed': False,
        'token': None
    })
