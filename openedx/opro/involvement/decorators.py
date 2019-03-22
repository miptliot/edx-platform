from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.http import urlquote
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment
from .utils import ask_enable_involvement


def check_involvement(func):
    def wrapper(self, request, course_id, chapter=None, section=None, position=None):
        course_key = CourseKey.from_string(course_id)
        if CourseEnrollment.is_enrolled(request.user, course_key) and ask_enable_involvement(course_id, request.user):
            next_page = urlquote(request.get_full_path())
            redirect_url = reverse('involvement:check-involvement', kwargs={'course_id': course_key})
            redirect_url = ''.join([redirect_url, '?next=', next_page])
            return HttpResponseRedirect(redirect_url)
        return func(self, request, course_id, chapter, section, position)
    return wrapper
