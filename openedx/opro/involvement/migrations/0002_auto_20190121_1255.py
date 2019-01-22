# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('involvement', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usercourseinvolvement',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='usercourseinvolvement',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='usercourseinvolvement',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='usercourseinvolvement',
            name='course_id',
        ),
    ]
