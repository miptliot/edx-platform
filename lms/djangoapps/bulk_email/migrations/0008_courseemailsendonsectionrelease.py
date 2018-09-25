# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulk_email', '0007_courseemaildelay'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseEmailSendOnSectionRelease',
            fields=[
                ('course_email', models.OneToOneField(related_name='section_release', primary_key=True, serialize=False, to='bulk_email.CourseEmail')),
                ('usage_key', models.CharField(max_length=255, db_index=True)),
                ('version_uuid', models.CharField(max_length=255)),
                ('start_datetime', models.DateTimeField(null=True)),
                ('removed', models.BooleanField(default=False)),
                ('sent', models.BooleanField(default=False)),
                ('post_data', models.TextField(default=b'{}', null=True, blank=True)),
            ],
        ),
    ]
