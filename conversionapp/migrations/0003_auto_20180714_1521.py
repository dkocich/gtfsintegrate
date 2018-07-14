# Generated by Django 2.0.6 on 2018-07-14 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conversionapp', '0002_correspondence_agency_correspondence_route'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExtraField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_name', models.CharField(max_length=50)),
                ('value', models.CharField(max_length=50)),
            ],
        ),
        migrations.RemoveField(
            model_name='correspondence_route',
            name='extra_data',
        ),
        migrations.AddField(
            model_name='correspondence_route',
            name='extra_data',
            field=models.ManyToManyField(to='conversionapp.ExtraField'),
        ),
    ]
