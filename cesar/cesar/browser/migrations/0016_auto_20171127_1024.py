# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-11-27 09:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0015_auto_20170802_1639'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sentence',
            name='sent',
            field=models.TextField(verbose_name='Sentence'),
        ),
    ]
