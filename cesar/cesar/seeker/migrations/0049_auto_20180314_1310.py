# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-03-14 12:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seeker', '0048_basket_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quantor',
            name='basket',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='myquantor', to='seeker.Basket'),
        ),
    ]
