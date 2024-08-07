# Generated by Django 2.2 on 2022-08-24 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doc', '0008_auto_20211129_1503'),
    ]

    operations = [
        migrations.CreateModel(
            name='Neologism',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stimulus', models.CharField(max_length=100, verbose_name='Lemma of word')),
                ('m', models.FloatField(default=0.0, verbose_name='Concrete m')),
                ('postag', models.CharField(blank=True, max_length=100, null=True, verbose_name='POS tag')),
            ],
        ),
    ]
