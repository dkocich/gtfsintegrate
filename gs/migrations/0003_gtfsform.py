# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-24 11:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gs', '0002_auto_20180524_1123'),
    ]

    operations = [
        migrations.CreateModel(
            name='GTFSForm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
            ],
        ),
    ]