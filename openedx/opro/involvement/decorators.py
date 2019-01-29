from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.http import urlquote
from opaque_keys.edx.keys import CourseKey
from .utils import ask_enable_involvement


def check_involvement(func):
    def wrapper(self, request, course_id, chapter=None, section=None, position=None):
        if ask_enable_involvement(course_id, request.user):
            next_page = urlquote(request.get_full_path())
            course_key = CourseKey.from_string(course_id)
            redirect_url = reverse('involvement:check-involvement', kwargs={'course_id': course_key})
            redirect_url = ''.join([redirect_url, '?next=', next_page])
            return HttpResponseRedirect(redirect_url)
        return func(self, request, course_id, chapter, section, position)
    return wrapper
