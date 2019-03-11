"""
Declares CourseUsageInfo class to be used by the transform method in
Transformers.
"""
from lms.djangoapps.courseware.access import _has_access_to_course
from course_shifts.models import CourseShift, course_shift_deadline
from django.conf import settings


class CourseUsageInfo(object):
    '''
    A class object that encapsulates the course and user context to be
    used as currency across block structure transformers, by passing
    an instance of it in calls to BlockStructureTransformer.transform
    methods.
    '''
    def __init__(self, course_key, user):
        # Course identifier (opaque_keys.edx.keys.CourseKey)
        self.course_key = course_key

        # User object (django.contrib.auth.models.User)
        self.user = user

        # Cached value of whether the user has staff access (bool/None)
        self._has_staff_access = None

        self._course_shift_init = False
        self._first_course_shift = None
        self._current_course_shift = None

    @property
    def has_staff_access(self):
        '''
        Returns whether the user has staff access to the course
        associated with this CourseUsageInfo instance.

        For performance reasons (minimizing multiple SQL calls), the
        value is cached within this instance.
        '''
        if self._has_staff_access is None:
            self._has_staff_access = _has_access_to_course(self.user, 'staff', self.course_key)
        return self._has_staff_access

    def course_shift_date(self, block_start_date):
        if settings.FEATURES.get("ENABLE_COURSE_SHIFTS", False):
            if not self._course_shift_init:
                try:
                    self._first_course_shift = CourseShift.objects.get(
                        course_key=self.course_key,
                        enabled=True,
                        studio_version=True)
                    self._current_course_shift = CourseShift.get_course_shift_by_current_date(self.course_key, self.user)
                except CourseShift.DoesNotExist:
                    pass
                self._course_shift_init = True
            if block_start_date and self._first_course_shift and self._current_course_shift:
                return course_shift_deadline(
                    self._current_course_shift.start_date,
                    self._first_course_shift.start_date,
                    block_start_date
                )
        return block_start_date

