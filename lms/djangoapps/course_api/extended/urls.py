"""
Course Block API URLs
"""
from django.conf import settings
from django.conf.urls import url

from .views import course_completion, course_progress

urlpatterns = [
    # This endpoint is an alternative to the above, but requires course_id as a parameter.
    url(
        r'^v1/completion/{course_key}'.format(course_key=settings.COURSE_ID_PATTERN),
        course_completion,
        name="completion_in_course"
    ),
    url(
        r'^v1/progress/{course_key}'.format(course_key=settings.COURSE_ID_PATTERN),
        course_progress,
        name="progress_in_course"
    )
]
