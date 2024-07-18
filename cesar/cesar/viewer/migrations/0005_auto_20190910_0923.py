# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-09-10 07:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0004_auto_20190828_1543'),
    ]

    operations = [
        migrations.AlterField(
            model_name='result',
            name='text',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='viewer.ResultText'),
        ),
        migrations.AlterField(
            model_name='resultfeatname',
            name='set',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='viewer.ResultSet'),
        ),
        migrations.AlterField(
            model_name='resultfeature',
            name='ftname',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='viewer.ResultFeatName'),
        ),
        migrations.AlterField(
            model_name='resultset',
            name='part',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='browser.Part'),
        ),
        migrations.AlterField(
            model_name='resulttext',
            name='general',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='viewer.ResultSet'),
        ),
        migrations.AlterField(
            model_name='resulttext',
            name='text',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='browser.Text'),
        ),
    ]