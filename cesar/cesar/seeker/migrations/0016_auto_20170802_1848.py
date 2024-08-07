# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-08-02 18:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seeker', '0015_auto_20170802_1639'),
    ]

    operations = [
        migrations.AddField(
            model_name='function',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='functionparent', to='seeker.Argument'),
        ),
        migrations.AddField(
            model_name='function',
            name='root',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='functionroot', to='seeker.ConstructionVariable'),
            preserve_default=False,
        ),
    ]
