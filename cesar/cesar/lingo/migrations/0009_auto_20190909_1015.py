# Generated by Django 2.0.4 on 2019-09-09 08:15

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('lingo', '0008_participant_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='participant',
            name='email',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='E-mailadres'),
        ),
        migrations.AlterField(
            model_name='response',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
