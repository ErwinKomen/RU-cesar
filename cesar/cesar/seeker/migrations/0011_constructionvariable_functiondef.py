# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-06 14:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seeker', '0010_auto_20170706_1347'),
    ]

    operations = [
        migrations.AddField(
            model_name='constructionvariable',
            name='functiondef',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='seeker.FunctionDef'),
        ),
    ]
