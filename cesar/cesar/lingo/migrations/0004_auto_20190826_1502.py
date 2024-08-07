# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2019-08-26 13:02
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lingo', '0003_qdata'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='created',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
        migrations.AddField(
            model_name='qdata',
            name='qcorr',
            field=models.CharField(blank=True, choices=[('n', 'No'), ('y', 'Yes')], default='', max_length=5, verbose_name='Topic response'),
        ),
        migrations.AddField(
            model_name='qdata',
            name='qtopic',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Topic'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='age',
            field=models.IntegerField(blank=True, null=True, verbose_name='Age (number)'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='edu',
            field=models.CharField(blank=True, choices=[('g1', '12th grade or less'), ('g4', "Associate's degree"), ('g5', "Bachelor's degree"), ('g8', 'Doctorate (PhD or EdD)'), ('g2', 'High school diploma or GED'), ('g6', "Master's degree"), ('g7', 'Professional degree (e.g. MD or JD)'), ('f3', 'Some college but no degree')], default='', max_length=5, verbose_name='Gender'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='engfirst',
            field=models.CharField(blank=True, choices=[('n', 'No'), ('y', 'Yes')], default='', max_length=5, verbose_name='English L1'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='gender',
            field=models.CharField(blank=True, choices=[('f', 'Female'), ('m', 'Male'), ('o', 'Other')], default='', max_length=5, verbose_name='Gender'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='lngfirst',
            field=models.CharField(blank=True, default='', max_length=200, null=True, verbose_name='First language'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='lngother',
            field=models.CharField(blank=True, default='', max_length=200, null=True, verbose_name='Other languages'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='ptcpid',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Survey participant ID'),
        ),
    ]
