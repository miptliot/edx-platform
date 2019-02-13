import datetime
import json

from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.utils.translation import ugettext as _
from pytz import UTC

from courseware.access import has_access
from student.models import CourseEnrollment
from .models import CourseShift, CourseShiftUser, allow_to_change_deadline, SHIFT_DATE_FORMAT
from util.json_request import JsonResponse
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


def check_course_exists(check_staff_permission=False):
    def check_course_exists(func):
        def wrapper(request, course_id):
            try:
                course_key = CourseKey.from_string(course_id)
                course = modulestore().get_course(course_key)
            except (InvalidKeyError, ItemNotFoundError):
                return JsonResponse({"success": False, "errorMessage": _("Course not found")}, status=404)
            if check_staff_permission:
                allow = has_access(request.user, 'staff', course)
                if allow:
                    return func(request, course)
                else:
                    return HttpResponseForbidden()
            else:
                return func(request, course)
        return wrapper
    return check_course_exists


@login_required
@check_course_exists(check_staff_permission=True)
def get_course_shifts(request, course):
    data = CourseShift.objects.filter(course_key=course.id).order_by('start_date', 'enrollment_start_date')
    return JsonResponse({"success": True, "data": [item.to_dict(add_number_of_students=True) for item in data]})


@login_required
@require_POST
@check_course_exists(check_staff_permission=True)
@transaction.atomic
def update_course_shifts(request, course):
    try:
        posted_data = json.loads(request.body.decode('utf-8'))
    except ValueError:
        return JsonResponse({"success": False, "errorMessage": _("Invalid request")})

    post_required_params = {
        'title': 'Course Shift',
        'startDate': 'Start Date',
        'enrollStartDate': 'Enrollment Start Date',
        'enrollEndDate': 'Enrollment End Date'
    }

    for k, v in post_required_params.iteritems():
        if k not in posted_data or posted_data[k].strip() == '':
            return JsonResponse({"success": False, "errorMessage": _(v + " field can't be empty")})

    name = posted_data['title'].strip()
    start_date = posted_data['startDate'].strip()
    enrollment_start_date = posted_data['enrollStartDate'].strip()
    enrollment_end_date = posted_data['enrollEndDate'].strip()

    if not name or not start_date or not enrollment_start_date or not enrollment_end_date:
        return JsonResponse({
            "success": False,
            "errorMessage": _("Some required fields were not passed")
        })

    try:
        course_shift_id = int(posted_data['id']) if 'id' in posted_data else None
    except ValueError:
        return JsonResponse({
            "success": False,
            "errorMessage": _("Invalid Course Shift ID format")
        })

    try:
        start_date = datetime.datetime.strptime(start_date, SHIFT_DATE_FORMAT).replace(tzinfo=UTC)
    except ValueError as e:
        return JsonResponse({
            "success": False,
            "errorMessage": _("Start date is invalid: ") + str(e)
        })

    try:
        enrollment_start_date = datetime.datetime.strptime(enrollment_start_date, SHIFT_DATE_FORMAT).replace(tzinfo=UTC)
    except ValueError as e:
        return JsonResponse({
            "success": False,
            "errorMessage": _("Enrollment start date is invalid: ") + str(e)
        })

    try:
        enrollment_end_date = datetime.datetime.strptime(enrollment_end_date, SHIFT_DATE_FORMAT).replace(tzinfo=UTC)
    except ValueError as e:
        return JsonResponse({
            "success": False,
            "errorMessage": _("Enrollment end date is invalid: ") + str(e)
        })

    if enrollment_start_date >= enrollment_end_date:
        return JsonResponse({
            "success": False,
            "errorMessage": _("Enrollment end date must be later than the enrollment start date")
        })

    if enrollment_start_date >= start_date:
        return JsonResponse({
            "success": False,
            "errorMessage": _("The course start date must be later than the enrollment start date")
        })

    #overlap_items = CourseShift.objects.filter(
    #    Q(course_key=course.id,
    #      enrollment_start_date__lte=enrollment_start_date,
    #      enrollment_end_date__gte=enrollment_start_date) |
    #    Q(course_key=course.id,
    #      enrollment_start_date__lte=enrollment_end_date,
    #      enrollment_end_date__gte=enrollment_end_date))
    #
    #if overlap_items:
    #    for overlap_item in overlap_items:
    #        if (course_shift_id and course_shift_id != overlap_item.id) or course_shift_id is None:
    #            overlap_item_dict = overlap_item.to_dict()
    #            return JsonResponse({
    #                "success": False,
    #                "errorMessage": _("New course shift interval overlaps with the interval for"
    #                                  " \"%(name)s\" (%(enrollment_start_date)s - %(enrollment_end_date)s)" % overlap_item_dict)
    #            })

    if course_shift_id:
        try:
            obj = CourseShift.objects.get(pk=course_shift_id, course_key=course.id)
            obj.name = name
            obj.start_date = start_date
            obj.enrollment_start_date = enrollment_start_date
            obj.enrollment_end_date = enrollment_end_date

            if obj.studio_version:
                return JsonResponse({"success": False, "errorMessage": _("This shift can't be modified")})
        except ObjectDoesNotExist:
            return JsonResponse({"success": False, "errorMessage": _("Course shift was not found")})
    else:
        obj = CourseShift(
            course_key=course.id,
            name=name,
            start_date=start_date,
            enrollment_start_date=enrollment_start_date,
            enrollment_end_date=enrollment_end_date,
            studio_version=False,
            enabled=True
        )
    obj.save()
    return JsonResponse({"success": True, "shift": obj.to_dict(add_number_of_students=True)})


@login_required
@check_course_exists(check_staff_permission=True)
def find_user(request, course):
    word = request.GET.get('word')
    word = word.strip()
    if not word:
        return JsonResponse({
            "success": False,
            "userid": None,
            "errorMessage": _("Invalid request")
        })

    try:
        user = User.objects.get(Q(username=word) | Q(email=word))
    except User.DoesNotExist:
        return JsonResponse({
            "success": False,
            "userid": None,
            "errorMessage": _("User not found")
        })

    enrollment = CourseEnrollment.get_enrollment(user, course.id)
    if not enrollment:
        return JsonResponse({
            "success": False,
            "userid": None,
            "errorMessage": _("User must be enrolled to the course")
        })

    try:
        obj = CourseShiftUser.objects.get(user=user, course_key=course.id)
        return JsonResponse({
            "success": True,
            "userid": user.id,
            "shift": obj.course_shift.to_dict()
        })
    except CourseShiftUser.DoesNotExist:
        return JsonResponse({
            "success": True,
            "userid": user.id,
            "shift": None
        })


@login_required
@require_POST
@check_course_exists(check_staff_permission=True)
@transaction.atomic
def update_user(request, course):
    try:
        posted_data = json.loads(request.body.decode('utf-8'))
    except ValueError:
        return JsonResponse({"success": False, "errorMessage": _("Invalid request")})

    try:
        user_id = posted_data.get('user_id', 0)
    except ValueError:
        user_id = 0

    try:
        course_shift_id = posted_data.get('course_shift_id', 0)
    except ValueError:
        course_shift_id = 0

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({
            "success": False,
            "errorMessage": _("User not found")
        })

    enrollment = CourseEnrollment.get_enrollment(user, course.id)
    if not enrollment:
        return JsonResponse({
            "success": False,
            "user_id": None,
            "errorMessage": _("User must be enrolled to the course")
        })

    try:
        course_shift = CourseShift.objects.get(pk=course_shift_id, course_key=course.id)
    except CourseShift.DoesNotExist:
        return JsonResponse({
            "success": False,
            "errorMessage": _("Course shift not found")
        })

    CourseShiftUser.objects.filter(user=user, course_key=course.id).delete()
    new_course_shift_user = CourseShiftUser(
        user=user,
        course_key=course.id,
        course_shift=course_shift)
    new_course_shift_user.save()

    return JsonResponse({
        "success": True,
        "shift": course_shift.to_dict()
    })


@login_required
@require_POST
@check_course_exists(check_staff_permission=False)
@transaction.atomic
def update_deadlines(request, course):
    enrollment = CourseEnrollment.get_enrollment(request.user, course.id)
    if not enrollment:
        return JsonResponse({
            "success": False,
            "errorMessage": _("User must be enrolled to the course")
        })

    allow, course_shift = allow_to_change_deadline(course.id, request.user)
    if allow:
        CourseShiftUser.objects.filter(user=request.user, course_key=course.id).delete()
        new_course_shift_user = CourseShiftUser(
            user=request.user,
            course_key=course.id,
            course_shift=course_shift)
        new_course_shift_user.save()
        return JsonResponse({
            "success": True,
            "msg": _("Your deadlines were successfully updated"),
            "id": new_course_shift_user.id
        })

    return JsonResponse({
        "success": False,
        "errorMessage": _("There is no available shifts")
    })
