# Generated by Django 3.2 on 2021-04-16 02:26

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1023)),
                ('role', models.IntegerField(choices=[(0, 'Supervisor'), (1, 'Instructor'), (2, 'TA')])),
                ('email', models.EmailField(max_length=254)),
                ('password', models.CharField(max_length=1023)),
                ('phone', models.CharField(max_length=1023)),
                ('address', models.CharField(max_length=1023)),
                ('office_hours', models.CharField(max_length=1023)),
            ],
        ),
    ]
