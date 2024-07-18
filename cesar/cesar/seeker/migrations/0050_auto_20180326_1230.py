# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-03-26 10:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seeker', '0049_auto_20180314_1310'),
    ]

    operations = [
        migrations.AddField(
            model_name='quantor',
            name='lines',
            field=models.IntegerField(blank=True, null=True, verbose_name='Number of lines'),
        ),
        migrations.AddField(
            model_name='quantor',
            name='words',
            field=models.IntegerField(blank=True, null=True, verbose_name='Number of words'),
        ),
    ]