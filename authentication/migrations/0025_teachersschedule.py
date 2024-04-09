# Generated by Django 4.2.10 on 2024-04-09 07:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0024_staffuser_first_name_staffuser_last_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeachersSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('schedule_data', models.JSONField(null=True)),
            ],
        ),
    ]
