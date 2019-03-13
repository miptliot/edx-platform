from rest_framework_oauth.authentication import OAuth2Authentication
from rest_framework.exceptions import APIException
from openedx.core.lib.api.permissions import ApiKeyHeaderPermission

from courseware.access import has_access
from util.json_request import JsonResponse
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


def check_course_exists(check_staff_permission=False):
    def check_course_exists(func):
        def wrapper(request, course_id):
            course = None
            try:
                course_key = CourseKey.from_string(course_id)
                course = modulestore().get_course(course_key)
            except (InvalidKeyError, ItemNotFoundError):
                pass

            if not course:
                return JsonResponse({"success": False, "error": "Course not found"}, status=404)

            if check_staff_permission:
                if ApiKeyHeaderPermission().has_permission(request, None):
                    return func(request, course)
                if request.user.is_authenticated:
                    user = request.user
                else:
                    user = None
                    msg = 'Invalid authorization params'
                    try:
                        auth_res = OAuth2Authentication().authenticate(request)
                        if auth_res is not None:
                            user = auth_res[0]
                    except APIException as e:
                        msg = msg + ': ' + str(e)
                    if not user:
                        return JsonResponse({"success": False, "error": msg}, status=403)

                allow = has_access(user, 'staff', course)
                if allow:
                    return func(request, course)
                else:
                    return JsonResponse({"success": False,
                                         "error": 'User have no permissions to access the course'}, status=403)
            else:
                return func(request, course)
        return wrapper
    return check_course_exists
