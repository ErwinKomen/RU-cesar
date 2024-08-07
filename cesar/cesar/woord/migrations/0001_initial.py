# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2021-03-18 12:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FieldChoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field', models.CharField(max_length=50)),
                ('english_name', models.CharField(max_length=100)),
                ('dutch_name', models.CharField(max_length=100)),
                ('abbr', models.CharField(default='-', max_length=20)),
                ('machine_value', models.IntegerField(help_text='The actual numeric value stored in the database. Created automatically.')),
            ],
            options={
                'ordering': ['field', 'machine_value'],
            },
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=10, verbose_name='Question tag')),
                ('judgment', models.IntegerField(default=0, verbose_name='Judgment')),
            ],
        ),
        migrations.CreateModel(
            name='WoordUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Full name')),
                ('gender', models.CharField(blank=True, choices=[('0', '-'), ('1', 'N/A')], default='', max_length=5, verbose_name='Gender')),
                ('age', models.IntegerField(blank=True, null=True, verbose_name='Age')),
                ('about', models.TextField(blank=True, null=True, verbose_name='User comments')),
                ('status', models.CharField(default='created', max_length=255, verbose_name='Status')),
            ],
        ),
        migrations.AddField(
            model_name='result',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='userresults', to='woord.WoordUser'),
        ),
    ]
