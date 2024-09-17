# Generated by Django 2.2.28 on 2024-07-18 10:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tsg', '0003_auto_20240711_1537'),
    ]

    operations = [
        migrations.CreateModel(
            name='TsgStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abbr', models.CharField(max_length=100, verbose_name='Abbreviation')),
                ('name', models.CharField(max_length=100, verbose_name='Full name')),
            ],
        ),
        migrations.AddField(
            model_name='tsghandle',
            name='tsgstatus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='statushandles', to='tsg.TsgStatus'),
        ),
    ]
