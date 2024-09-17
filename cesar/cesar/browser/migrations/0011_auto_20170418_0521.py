# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-04-18 05:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0010_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='download',
            name='count',
            field=models.CharField(default='unknown', max_length=10, verbose_name='Number of texts'),
        ),
        migrations.AddField(
            model_name='text',
            name='author',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Author(s) of this text'),
        ),
        migrations.AddField(
            model_name='text',
            name='date',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Publication year of this text'),
        ),
        migrations.AddField(
            model_name='text',
            name='genre',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Genre of this text'),
        ),
        migrations.AddField(
            model_name='text',
            name='subtype',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Subtype of this text'),
        ),
        migrations.AlterField(
            model_name='download',
            name='part',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='downloads', to='browser.Part'),
        ),
        migrations.AlterField(
            model_name='download',
            name='url',
            field=models.URLField(blank=True, null=True, verbose_name='Link to download this corpus (part)'),
        ),
    ]
