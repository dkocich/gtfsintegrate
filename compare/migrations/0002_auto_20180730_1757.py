# Generated by Django 2.0.6 on 2018-07-30 17:57

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compare', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relation_data',
            name='all_node_info',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=250), blank=True, null=True, size=None), blank=True, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='relation_data',
            name='relation_info',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=250, null=True), size=None), blank=True, null=True, size=None),
        ),
    ]
