# Generated by Django 2.0.4 on 2019-09-09 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lingo', '0010_qdata_include'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='ip',
            field=models.CharField(blank=True, default='unknown', max_length=200, verbose_name='IP address'),
        ),
    ]
