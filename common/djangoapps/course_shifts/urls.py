from django.conf import settings
from django.conf.urls import url
from .views import get_course_shifts, update_course_shifts, find_user, update_user, update_deadlines


urlpatterns = [
    url(r'^get-course-shifts/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        get_course_shifts, name='get-course-shifts'),
    url(r'^update-course-shifts/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        update_course_shifts, name='update-course-shifts'),
    url(r'^find-user/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        find_user, name='find-user-and-course-shifts'),
    url(r'^update-user/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        update_user, name='update-user-course-shift'),
    url(r'^update-deadlines/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        update_deadlines, name='update-deadlines-course-shift')
]
