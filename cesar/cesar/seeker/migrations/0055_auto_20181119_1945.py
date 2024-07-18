# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-11-19 18:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seeker', '0054_auto_20180625_1450'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchmain',
            name='category',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Constituent category'),
        ),
        migrations.AddField(
            model_name='searchmain',
            name='lemma',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Lemma'),
        ),
        migrations.AlterField(
            model_name='research',
            name='targetType',
            field=models.CharField(choices=[('0', '----'), ('w', 'Word(s)'), ('c', 'Constituent(s)'), ('e', 'Extended')], max_length=5, verbose_name='Main element type'),
        ),
    ]