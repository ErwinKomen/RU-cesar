# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2021-03-29 11:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('woord', '0013_questionset_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='choice',
            name='valid',
            field=models.BooleanField(default=True, verbose_name='Valid'),
        ),
    ]
