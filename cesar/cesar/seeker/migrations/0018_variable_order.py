# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-08-16 08:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seeker', '0017_auto_20170809_1106'),
    ]

    operations = [
        migrations.AddField(
            model_name='variable',
            name='order',
            field=models.IntegerField(default=0, verbose_name='Order'),
        ),
    ]