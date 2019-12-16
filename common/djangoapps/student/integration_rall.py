import requests
from functools import wraps

from django.conf import settings
from django.http import Http404
from django.utils.translation import ugettext as _
from student.models import CourseEnrollment
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from xmodule.modulestore.django import modulestore


def check_integration_rall(view_func):
    @wraps(view_func)
    def inner(request, *args, **kwargs):
        course_id = None
        for arg in args:
            if arg.startswith(CourseLocator.CANONICAL_NAMESPACE):
                course_id = arg
                break
        if not course_id:
            course_id = kwargs.get('course_id')
        if course_id:
            course = modulestore().get_course(CourseKey.from_string(course_id))
            if course.enable_integration_2035_univ \
              and request.user.is_authenticated \
              and not CourseEnrollment.is_enrolled(request.user, course.id)\
              and not request.user.profile.get_unti_id():
                raise Http404
        return view_func(request, *args, **kwargs)
    return inner


def check_can_rall_enroll(request, course_id):
    can_enroll = False
    msg = ''

    if request.user.is_authenticated:
        unti_id = request.user.profile.get_unti_id()
        if unti_id:
            api_rall = ApiRall()
            status_code, result = api_rall.enroll_check(unti_id, course_id)
            if status_code == 200:
                can_enroll = True
            elif status_code == 403 and result and 'message' in result:
                msg = _("You can't enroll through 20.35:") + ' ' + result['message']
            else:
                msg = _("You can't enroll through 20.35: Unknown server error")
        else:
            msg = _('Course available only for the 20.35 students')
    else:
        msg = _('Course available only for authorized users')
    return can_enroll, msg


def rall_enroll(request, course_id):
    success = False
    if request.user.is_authenticated:
        unti_id = request.user.profile.get_unti_id()
        api_rall = ApiRall()
        status_code, result = api_rall.enroll(unti_id, course_id)
        if status_code == 201:
            success = True
    return success


class ApiRall(object):
    _platform_id = None
    _host = None
    _token = None

    def __init__(self):
        self._host = configuration_helpers.get_value('RALL_URL', settings.RALL_URL)
        self._token = configuration_helpers.get_value('RALL_API_TOKEN', settings.RALL_API_TOKEN)
        self._platform_id = configuration_helpers.get_value('RALL_PLATFORM_ID', settings.RALL_PLATFORM_ID)

    def _send_request(self, api_part, course_id, unti_id, is_post=False):
        url = self._host + '/api/v1' + api_part
        payload = {
            'platform_id': str(self._platform_id) if self._platform_id else '',
            'unti_id': int(unti_id),
            'external_course_id': str(course_id)
        }
        headers = {'Authorization': 'Token ' + self._token, 'Accept': 'application/json'}

        if is_post:
            headers['Content-Type'] = 'application/json'
            r = requests.post(url, data=payload, headers=headers)
        else:
            r = requests.get(url, params=payload, headers=headers)

        try:
            content = r.json() if r.content else None
        except (ValueError, TypeError):
            content = None

        return r.status_code, content

    def enroll_check(self, unti_id, course_id):
        return self._send_request('/course/enroll/check/', course_id, unti_id)

    def enroll(self, unti_id, course_id):
        return self._send_request('/course/enroll/', course_id, unti_id, is_post=True)


