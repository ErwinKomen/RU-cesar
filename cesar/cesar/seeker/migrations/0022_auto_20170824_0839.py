# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-08-24 08:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seeker', '0021_auto_20170824_0604'),
    ]

    operations = [
        migrations.AddField(
            model_name='function',
            name='type',
            field=models.CharField(blank=True, choices=[('2', 'Boolean'), ('3', 'Constituent'), ('1', 'Integer'), ('0', 'String')], help_text='Sorry, no help available for search.type', max_length=5, verbose_name='Type'),
        ),
        migrations.AddField(
            model_name='functiondef',
            name='type',
            field=models.CharField(blank=True, choices=[('2', 'Boolean'), ('3', 'Constituent'), ('1', 'Integer'), ('0', 'String')], help_text='Sorry, no help available for search.type', max_length=5, verbose_name='Type'),
        ),
        migrations.AddField(
            model_name='variable',
            name='type',
            field=models.CharField(blank=True, choices=[('2', 'Boolean'), ('3', 'Constituent'), ('1', 'Integer'), ('0', 'String')], help_text='Sorry, no help available for search.type', max_length=5, verbose_name='Type'),
        ),
        migrations.AlterField(
            model_name='condition',
            name='condtype',
            field=models.CharField(choices=[('dvar', 'Data-dependant variable'), ('func', 'Function')], help_text='Sorry, no help available for search.condtype', max_length=5, verbose_name='Condition type'),
        ),
        migrations.AlterField(
            model_name='variable',
            name='description',
            field=models.TextField(verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='variable',
            name='name',
            field=models.CharField(max_length=50, verbose_name='Name'),
        ),
    ]
