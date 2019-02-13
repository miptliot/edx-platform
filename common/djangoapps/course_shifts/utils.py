from django.conf import settings


def course_shifts_enabled(course):
    return settings.FEATURES.get("ENABLE_COURSE_SHIFTS", False) and course.enable_course_shifts
