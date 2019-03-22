# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations
from opaque_keys.edx.django.models import UsageKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('involvement', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='involvementlink',
            name='usage_key',
            field=UsageKeyField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='involvementlink',
            unique_together=set([('user', 'usage_key')]),
        ),
    ]
