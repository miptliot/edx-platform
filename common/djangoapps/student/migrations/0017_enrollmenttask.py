# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-08-08 23:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0016_coursenrollment_course_on_delete_do_nothing'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnrollmentTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('task_uuid', models.CharField(db_index=True, max_length=255)),
                ('course_id', opaque_keys.edx.django.models.CourseKeyField(db_index=True, max_length=255)),
                ('request_data', models.TextField(blank=True)),
                ('result_data', models.TextField(blank=True)),
                ('status', models.CharField(choices=[(b'not_started', b'Not Started'), (b'started', b'Started'), (b'finished', b'Finished'), (b'error', b'Error')], default=b'not_started', max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
