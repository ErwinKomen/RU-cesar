# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2021-06-10 08:22
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('doc', '0004_auto_20200528_1351'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foliadocs',
            name='owner',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='owner_foliadocs', to=settings.AUTH_USER_MODEL),
        ),
    ]