# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-03-16 10:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lingo', '0015_participant_teaches'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='responsecount',
            field=models.IntegerField(default=10, verbose_name='Number of responses per participant'),
        ),
    ]
