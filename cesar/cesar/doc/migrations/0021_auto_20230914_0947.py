# Generated by Django 2.2 on 2023-09-14 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doc', '0020_froglink_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='froglink',
            name='size',
            field=models.IntegerField(blank=True, null=True, verbose_name='Size of text (words)'),
        ),
    ]