# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='InvolvementLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_key', CourseKeyField(max_length=255, db_index=True)),
                ('usage_key', UsageKeyField(unique=True, max_length=255)),
                ('block_type', models.CharField(max_length=32)),
                ('link_id', models.CharField(unique=True, max_length=255)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserCourseInvolvement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_key', CourseKeyField(max_length=255, db_index=True)),
                ('is_active', models.BooleanField(default=True)),
                ('last_action_time', models.DateTimeField(null=True, blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserVisitInvolvementLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('visit_id', models.CharField(max_length=255, db_index=True)),
                ('visit_time', models.DateTimeField(null=True, blank=True)),
                ('link', models.ForeignKey(to='involvement.InvolvementLink')),
            ],
        ),
    ]
