# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2021-03-25 08:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('woord', '0003_auto_20210325_0904'),
    ]

    operations = [
        migrations.AlterField(
            model_name='result',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questionresults', to='woord.Question'),
        ),
    ]
