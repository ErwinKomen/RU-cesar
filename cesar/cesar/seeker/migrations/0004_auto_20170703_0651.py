# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-07-03 06:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seeker', '0003_auto_20170630_1341'),
    ]

    operations = [
        migrations.RenameField(
            model_name='constructionvariable',
            old_name='value',
            new_name='svalue',
        ),
        migrations.AddField(
            model_name='constructionvariable',
            name='type',
            field=models.CharField(default=0, help_text='Sorry, no help available for search.variabletype', max_length=5, verbose_name='Variable type'),
            preserve_default=False,
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
    ]