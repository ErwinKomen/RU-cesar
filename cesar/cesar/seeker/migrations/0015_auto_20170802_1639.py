# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-08-02 16:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seeker', '0014_auto_20170802_1240'),
    ]

    operations = [
        migrations.AlterField(
            model_name='argument',
            name='argtype',
            field=models.CharField(choices=[('cnst', 'Constituent'), ('cvar', 'Construction variable'), ('fixed', 'Fixed value'), ('func', 'Function output'), ('gvar', 'Global variable'), ('axis', 'Hierarchical relation')], help_text='Sorry, no help available for search.argtype', max_length=5, verbose_name='Variable type'),
        ),
        migrations.AlterField(
            model_name='argumentdef',
            name='argtype',
            field=models.CharField(choices=[('cnst', 'Constituent'), ('cvar', 'Construction variable'), ('fixed', 'Fixed value'), ('func', 'Function output'), ('gvar', 'Global variable'), ('axis', 'Hierarchical relation')], help_text='Sorry, no help available for search.argtype', max_length=5, verbose_name='Variable type'),
        ),
        migrations.AlterField(
            model_name='constructionvariable',
            name='type',
            field=models.CharField(choices=[('calc', 'Calculate'), ('fixed', 'Fixed value'), ('gvar', 'Global variable')], help_text='Sorry, no help available for search.variabletype', max_length=5, verbose_name='Variable type'),
        ),
        migrations.AlterField(
            model_name='searchitem',
            name='function',
            field=models.CharField(choices=[('0', 'word-group')], help_text='Sorry, no help available for search.function', max_length=5, verbose_name='Format for this corpus (part)'),
        ),
        migrations.AlterField(
            model_name='searchitem',
            name='operator',
            field=models.CharField(choices=[('0', 'groupmatches')], help_text='Sorry, no help available for search.operator', max_length=5, verbose_name='Operator'),
        ),
        migrations.AlterField(
            model_name='searchmain',
            name='function',
            field=models.CharField(choices=[('0', 'word-group')], help_text='Sorry, no help available for search.function', max_length=5, verbose_name='Format for this corpus (part)'),
        ),
        migrations.AlterField(
            model_name='searchmain',
            name='operator',
            field=models.CharField(choices=[('0', 'groupmatches')], help_text='Sorry, no help available for search.operator', max_length=5, verbose_name='Operator'),
        ),
        migrations.AlterField(
            model_name='sharegroup',
            name='permission',
            field=models.CharField(help_text='Sorry, no help available for search.permission', max_length=5, verbose_name='Permissions'),
        ),
    ]
