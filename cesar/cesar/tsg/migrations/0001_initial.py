# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-06-27 10:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TsgHandle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=100, verbose_name='Handle code')),
                ('url', models.URLField(verbose_name='Handle URL')),
                ('domain', models.CharField(default='21.11114', max_length=100, verbose_name='Handle base url')),
                ('info', models.TextField(default='[]', verbose_name='Information')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('history', models.TextField(default='[]', verbose_name='History')),
            ],
        ),
        migrations.CreateModel(
            name='TsgInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('infokey', models.CharField(max_length=100, verbose_name='Key to this bit of information')),
                ('infoval', models.TextField(blank=True, default='', verbose_name='The information itself')),
                ('history', models.TextField(default='[]', verbose_name='History')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
