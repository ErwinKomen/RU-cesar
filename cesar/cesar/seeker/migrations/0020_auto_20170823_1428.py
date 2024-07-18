# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-08-23 14:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seeker', '0019_auto_20170816_1055'),
    ]

    operations = [
        migrations.CreateModel(
            name='Condition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Name')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('condtype', models.CharField(help_text='Sorry, no help available for search.condtype', max_length=5, verbose_name='Condition type')),
                ('cvar', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cvarcondition', to='seeker.ConstructionVariable')),
                ('function', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='functioncondition', to='seeker.Function')),
                ('functiondef', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='functiondefcondition', to='seeker.FunctionDef')),
                ('gateway', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conditions', to='seeker.Gateway')),
            ],
        ),
        migrations.AlterField(
            model_name='argument',
            name='argtype',
            field=models.CharField(choices=[('cnst', 'Constituent'), ('cvar', 'Construction variable'), ('fixed', 'Fixed value'), ('func', 'Function output'), ('gvar', 'Global variable'), ('axis', 'Hierarchical relation'), ('hit', 'Search hit')], help_text='Sorry, no help available for search.argtype', max_length=5, verbose_name='Variable type'),
        ),
        migrations.AlterField(
            model_name='argumentdef',
            name='argtype',
            field=models.CharField(choices=[('cnst', 'Constituent'), ('cvar', 'Construction variable'), ('fixed', 'Fixed value'), ('func', 'Function output'), ('gvar', 'Global variable'), ('axis', 'Hierarchical relation'), ('hit', 'Search hit')], help_text='Sorry, no help available for search.argtype', max_length=5, verbose_name='Variable type'),
        ),
    ]
