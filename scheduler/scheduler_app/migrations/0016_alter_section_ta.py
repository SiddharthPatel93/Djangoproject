# Generated by Django 3.2.3 on 2021-05-18 05:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler_app', '0015_merge_0014_auto_20210516_1506_0014_auto_20210516_2046'),
    ]

    operations = [
        migrations.AlterField(
            model_name='section',
            name='ta',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ta', to='scheduler_app.account'),
        ),
    ]