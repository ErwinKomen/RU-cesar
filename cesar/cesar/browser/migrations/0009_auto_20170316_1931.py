# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-16 18:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0008_status_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='corpus',
            name='metavar',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='browser.Metavar'),
        ),
    ]