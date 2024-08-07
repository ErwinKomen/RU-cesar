# Generated by Django 2.2 on 2023-01-16 14:54

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('doc', '0014_worddef_wordlist'),
    ]

    operations = [
        migrations.AddField(
            model_name='wordlist',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='wordlist',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='wordlist',
            name='saved',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
