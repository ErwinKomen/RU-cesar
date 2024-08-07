# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-08-31 07:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seeker', '0022_auto_20170824_0839'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sharegroup',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.Group'),
        ),
        migrations.AlterField(
            model_name='sharegroup',
            name='permission',
            field=models.CharField(choices=[('n', 'None'), ('rw', 'Reading and writing'), ('r', 'reading')], help_text='Sorry, no help available for search.permission', max_length=5, verbose_name='Permissions'),
        ),
    ]
