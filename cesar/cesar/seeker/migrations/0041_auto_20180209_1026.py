# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-02-09 09:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seeker', '0040_function_line'),
    ]

    operations = [
        migrations.CreateModel(
            name='Axis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Name')),
                ('xpath', models.TextField(default='.', verbose_name='Implementation')),
            ],
        ),
        migrations.AddField(
            model_name='argumentdef',
            name='hasoutputtype',
            field=models.BooleanField(default=False, verbose_name='This type equals outputtype'),
        ),
        migrations.AlterField(
            model_name='argument',
            name='argtype',
            field=models.CharField(choices=[('cnst', 'Constituent'), ('cvar', 'Construction variable'), ('dvar', 'Data-dependant variable'), ('fixed', 'Fixed value'), ('func', 'Function output'), ('gvar', 'Global variable'), ('axis', 'Hierarchical relation'), ('rel', 'Relation'), ('hit', 'Search hit')], help_text='Sorry, no help available for search.argtype', max_length=5, verbose_name='Variable type'),
        ),
        migrations.AlterField(
            model_name='argumentdef',
            name='argtype',
            field=models.CharField(choices=[('cnst', 'Constituent'), ('cvar', 'Construction variable'), ('dvar', 'Data-dependant variable'), ('fixed', 'Fixed value'), ('func', 'Function output'), ('gvar', 'Global variable'), ('axis', 'Hierarchical relation'), ('rel', 'Relation'), ('hit', 'Search hit')], help_text='Sorry, no help available for search.argtype', max_length=5, verbose_name='Variable type'),
        ),
        migrations.AddField(
            model_name='argument',
            name='axis',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='seeker.Axis'),
        ),
    ]
