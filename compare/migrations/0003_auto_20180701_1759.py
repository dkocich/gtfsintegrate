# Generated by Django 2.0.6 on 2018-07-01 17:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compare', '0002_osm_node_cmp'),
    ]

    operations = [
        migrations.RenameField(
            model_name='osm_node_cmp',
            old_name='feed_id',
            new_name='feed',
        ),
    ]