# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2021-03-25 14:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('woord', '0008_auto_20210325_1506'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Stimuli',
            new_name='Stimulus',
        ),
        migrations.RemoveField(
            model_name='question',
            name='stimuli',
        ),
        migrations.AddField(
            model_name='question',
            name='stimulus',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='stimulusquestions', to='woord.Stimulus'),
            preserve_default=False,
        ),
    ]
