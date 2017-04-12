import logging
from collections import OrderedDict
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils.translation import ugettext as _
from util.json_request import JsonResponse, JsonResponseBadRequest
from opaque_keys.edx.keys import CourseKey
from .utils import are_change_due_keys_broken
from .tasks import submit_change_due_task

log = logging.getLogger(__name__)


@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
def post_change_due(request, course_id):
    """ Changes due dates for given cohort/user for given block/course"""
    data = request.POST
    params = OrderedDict()
    if 'user' in data['who']:
        if not data['user-name']:
            return JsonResponse({"message": _("User is not specified")}, status=400)
        params['user'] = data['user-name']
    if 'cohort' in data['who']:
        try:
            params['cohort'] = data['cohort']
        except:
            return JsonResponse({"message": _("Cohort is not specified")}, status=400)
    if 'course' in data['where']:
        params['course_key'] = course_id
    if 'block' in data['where']:
        if not data['location']:
            return JsonResponse({"message": _("Location is not specified")}, status=400)
        params['block_key'] = data['location']

    if 'add' in data['when']:
        if not data['add-days']:
            return JsonResponse({"message": _("Days to add are not specified")}, status=400)
        params['add_days'] = data['add-days']
    if 'set' in data['when']:
        if not data['set-date']:
            return JsonResponse({"message": _("Date is not specified")}, status=400)
        params['set_date'] = data['set-date']
    course_key = CourseKey.from_string(course_id)
    failed_check = are_change_due_keys_broken(params, course_key)
    if failed_check:
        return JsonResponse({"message": failed_check}, status=400)

    submit_change_due_task(request, course_key, params)
    return JsonResponse(status=200)
