# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-11-19 18:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0020_auto_20180605_0914'),
    ]

    operations = [
        migrations.AlterField(
            model_name='corpus',
            name='lng',
            field=models.CharField(choices=[('3', 'che_lat'), ('0', 'eng_hist'), ('4', 'eng_penta'), ('5', 'eng_sla'), ('1', 'lak_cyr'), ('2', 'nld'), ('6', 'nld_hist')], help_text='Sorry, no help available for corpus.language', max_length=5, verbose_name='Language of the texts'),
        ),
    ]
