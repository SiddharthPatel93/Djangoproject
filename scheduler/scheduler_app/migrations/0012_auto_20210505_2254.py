# Generated by Django 3.2.1 on 2021-05-06 03:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler_app', '0011_auto_20210505_2052'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='address',
            field=models.CharField(blank=True, default='', max_length=1023),
        ),
        migrations.AlterField(
            model_name='account',
            name='office_hours',
            field=models.CharField(blank=True, default='', max_length=1023),
        ),
        migrations.AlterField(
            model_name='account',
            name='phone',
            field=models.CharField(blank=True, default='', max_length=1023),
        ),
        migrations.AlterField(
            model_name='account',
            name='skills',
            field=models.CharField(blank=True, default='', max_length=1023),
        ),
    ]