# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-08-31 10:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seeker', '0024_auto_20170831_0846'),
    ]

    operations = [
        migrations.AddField(
            model_name='argument',
            name='dvar',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='seeker.VarDef'),
        ),
        migrations.AlterField(
            model_name='argument',
            name='argtype',
            field=models.CharField(choices=[('cnst', 'Constituent'), ('cvar', 'Construction variable'), ('dvar', 'Data-dependant variable'), ('fixed', 'Fixed value'), ('func', 'Function output'), ('gvar', 'Global variable'), ('axis', 'Hierarchical relation'), ('hit', 'Search hit')], help_text='Sorry, no help available for search.argtype', max_length=5, verbose_name='Variable type'),
        ),
        migrations.AlterField(
            model_name='argumentdef',
            name='argtype',
            field=models.CharField(choices=[('cnst', 'Constituent'), ('cvar', 'Construction variable'), ('dvar', 'Data-dependant variable'), ('fixed', 'Fixed value'), ('func', 'Function output'), ('gvar', 'Global variable'), ('axis', 'Hierarchical relation'), ('hit', 'Search hit')], help_text='Sorry, no help available for search.argtype', max_length=5, verbose_name='Variable type'),
        ),
    ]
