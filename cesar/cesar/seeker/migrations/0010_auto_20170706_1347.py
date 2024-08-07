# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-07-06 13:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seeker', '0009_auto_20170706_0428'),
    ]

    operations = [
        migrations.AlterField(
            model_name='constructionvariable',
            name='function',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='seeker.Function'),
        ),
        migrations.AlterField(
            model_name='constructionvariable',
            name='type',
            field=models.CharField(choices=[('1', 'Calculate'), ('0', 'Fixed value'), ('2', 'Global variable')], help_text='Sorry, no help available for search.variabletype', max_length=5, verbose_name='Variable type'),
        ),
    ]
