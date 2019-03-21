from django.contrib.auth.models import User
from django.db import models
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField, UsageKeyField


class InvolvementLink(models.Model):
    course_key = CourseKeyField(max_length=255, db_index=True)
    usage_key = UsageKeyField(max_length=255)
    block_type = models.CharField(max_length=32, null=False, blank=False)
    link_id = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User)

    class Meta(object):
        unique_together = (('user', 'usage_key'),)

class UserVisitInvolvementLink(models.Model):
    link = models.ForeignKey(InvolvementLink)
    visit_id = models.CharField(max_length=255, db_index=True)
    visit_time = models.DateTimeField(null=True, blank=True)


class UserCourseInvolvement(models.Model):
    user = models.ForeignKey(User)
    course_key = CourseKeyField(max_length=255, db_index=True)
    is_active = models.BooleanField(default=True)
    last_action_time = models.DateTimeField(null=True, blank=True)
