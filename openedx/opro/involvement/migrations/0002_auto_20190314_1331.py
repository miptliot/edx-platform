# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import openedx.core.djangoapps.xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        ('involvement', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='involvementlink',
            name='usage_key',
            field=openedx.core.djangoapps.xmodule_django.models.UsageKeyField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='involvementlink',
            unique_together=set([('user', 'usage_key')]),
        ),
    ]
