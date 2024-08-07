# Generated by Django 2.2 on 2023-09-14 13:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('doc', '0021_auto_20230914_0947'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comparison',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='base_comparisons', to='doc.FrogLink')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target_comparisons', to='doc.FrogLink')),
            ],
        ),
        migrations.AddField(
            model_name='froglink',
            name='comparisons',
            field=models.ManyToManyField(through='doc.Comparison', to='doc.FrogLink'),
        ),
    ]
