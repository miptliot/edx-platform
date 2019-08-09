"""
URLs for the Enrollment API

"""
from django.conf import settings
from django.conf.urls import url

from .views import EnrollmentCourseDetailView, EnrollmentListView, BatchEnrollmentView, EnrollmentView, UnenrollmentView

urlpatterns = [
    url(r'^enrollment/{username},{course_key}$'.format(
        username=settings.USERNAME_PATTERN,
        course_key=settings.COURSE_ID_PATTERN),
        EnrollmentView.as_view(), name='courseenrollment'),
    url(r'^enrollment/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        EnrollmentView.as_view(), name='courseenrollment'),
    url(r'^enrollment$', EnrollmentListView.as_view(), name='courseenrollments'),
    url(r'^batch_enrollment/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        BatchEnrollmentView.as_view(), name='batch_courseenrollments'),
    url(r'^course/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        EnrollmentCourseDetailView.as_view(), name='courseenrollmentdetails'),
    url(r'^unenroll/$', UnenrollmentView.as_view(), name='unenrollment'),
]
