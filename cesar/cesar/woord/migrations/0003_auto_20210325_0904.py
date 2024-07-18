# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2021-03-25 08:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('woord', '0002_auto_20210323_1153'),
    ]

    operations = [
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('left', models.CharField(max_length=255, verbose_name='Left')),
                ('right', models.CharField(max_length=255, verbose_name='Right')),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('woord', models.CharField(max_length=255, verbose_name='Woord')),
                ('category', models.CharField(max_length=255, verbose_name='Category')),
                ('choice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='choicequestions', to='woord.Choice')),
            ],
        ),
        migrations.CreateModel(
            name='Stimuli',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
            ],
        ),
        migrations.AddField(
            model_name='woorduser',
            name='history',
            field=models.TextField(default='[]', verbose_name='History'),
        ),
        migrations.AddField(
            model_name='question',
            name='stimuli',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stimuliquestions', to='woord.Stimuli'),
        ),
    ]
