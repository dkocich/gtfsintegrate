# Generated by Django 2.0.6 on 2018-07-14 16:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conversionapp', '0003_auto_20180714_1521'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extrafield',
            name='field_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='extrafield',
            name='value',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
