# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-10-09 06:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0015_auto_20170802_1639'),
        ('seeker', '0029_auto_20170925_1501'),
    ]

    operations = [
        migrations.CreateModel(
            name='Basket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('format', models.CharField(choices=[('-', 'folia'), ('-', 'psdx')], help_text='Sorry, no help available for corpus.format', max_length=5, verbose_name='XML format')),
                ('codedef', models.TextField(blank=True, verbose_name='Xquery definitions')),
                ('codeqry', models.TextField(blank=True, verbose_name='Xquery main query')),
                ('status', models.CharField(max_length=200, verbose_name='Status')),
                ('jobid', models.CharField(blank=True, max_length=50, verbose_name='Job identifier')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('saved', models.DateTimeField(blank=True, null=True)),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='browser.Part')),
                ('research', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='baskets', to='seeker.Research')),
            ],
        ),
    ]
