# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-01-16 08:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lingo', '0012_auto_20200116_0825'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='metafields',
            field=models.TextField(blank=True, default='{}', verbose_name='Participant metadata'),
        ),
    ]
