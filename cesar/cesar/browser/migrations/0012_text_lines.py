# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-04-18 19:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0011_auto_20170418_0521'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='lines',
            field=models.IntegerField(default=0, verbose_name='Number of lines'),
        ),
    ]