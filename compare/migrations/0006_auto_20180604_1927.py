# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-04 19:27
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compare', '0005_auto_20180604_1920'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cmp_stop',
            old_name='geom',
            new_name='stop_geom',
        ),
    ]