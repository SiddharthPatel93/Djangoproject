# Generated by Django 3.2 on 2021-04-27 17:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler_app', '0008_merge_20210427_1253'),
    ]

    operations = [
        migrations.RenameField(
            model_name='section',
            old_name='TA',
            new_name='ta',
        ),
    ]