# Generated by Django 2.2 on 2021-10-07 07:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('woord', '0014_choice_valid'),
    ]

    operations = [
        migrations.AddField(
            model_name='stimulus',
            name='note',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Note'),
        ),
    ]