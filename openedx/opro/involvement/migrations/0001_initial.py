# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import openedx.core.djangoapps.xmodule_django.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseInvolvement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('module_type', models.CharField(default=b'disabled', max_length=32, db_index=True, choices=[(b'disabled', b'disabled'), (b'optional', b'optional'), (b'required', b'required')])),
                ('course_id', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255, verbose_name='Course', db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='InvolvementLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('link_id', models.CharField(unique=True, max_length=64, db_index=True)),
                ('course_key', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('usage_key', openedx.core.djangoapps.xmodule_django.models.UsageKeyField(max_length=255, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserCourseInvolvement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserVisitInvolvementLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('link', models.ForeignKey(to='involvement.InvolvementLink')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='involvementlink',
            unique_together=set([('usage_key', 'link_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='usercourseinvolvement',
            unique_together=set([('user', 'course_id')]),
        ),
    ]
