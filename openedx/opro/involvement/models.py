from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField, UsageKeyField


class CourseInvolvement(models.Model):
    """
    This object indicates is involvement enabled for course
    """
    INVOLVEMENT_OPTIONS = (('disabled', 'disabled'),
                    ('optional', 'optional'),
                    ('required', 'required'))
    module_type = models.CharField(max_length=32, choices=INVOLVEMENT_OPTIONS, default='disabled', db_index=True)
    course_id = CourseKeyField(max_length=255, db_index=True, verbose_name=_("Course"))


class InvolvementLink(models.Model):
    """
    Pairs (external link_id, internal usage_key)
    """
    link_id = models.CharField(max_length=64, unique=True, db_index=True)
    course_key = CourseKeyField(max_length=255, db_index=True)
    usage_key = UsageKeyField(max_length=255, db_index=True)

    class Meta(object):
        unique_together = (('usage_key', 'link_id'),)


class UserCourseInvolvement(models.Model):
    """
    Represents a Student's Involvement collection approved.
    """
    user = models.OneToOneField(User)
    is_active = models.BooleanField(default=True)


class UserVisitInvolvementLink(models.Model):
    """
    Store all visits on pages with InvolvementLink
    """
    link = models.ForeignKey(InvolvementLink)
    user = models.ForeignKey(User)
