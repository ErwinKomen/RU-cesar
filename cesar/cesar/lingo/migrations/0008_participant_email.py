# Generated by Django 2.0.4 on 2019-09-09 07:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lingo', '0007_auto_20190905_1516'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='email',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='E-maladres'),
        ),
    ]