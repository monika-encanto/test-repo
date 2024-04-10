# Generated by Django 4.2.10 on 2024-04-10 05:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusRoute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('route_name', models.CharField(max_length=100)),
                ('primary_start_time', models.TimeField()),
                ('primary_start_stop', models.CharField(max_length=100)),
                ('primary_next_stop', models.JSONField(null=True)),
                ('alternate_start_time', models.TimeField(blank=True, null=True)),
                ('alternate_next_stop', models.JSONField(blank=True, null=True)),
                ('bus', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bus.bus')),
            ],
        ),
    ]
