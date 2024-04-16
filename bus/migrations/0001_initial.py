# Generated by Django 4.2.10 on 2024-04-10 05:41

from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bus_image', models.ImageField(blank=True, upload_to='')),
                ('bus_number', models.CharField(max_length=20, unique=True)),
                ('driver_name', models.CharField(max_length=100)),
                ('driver_gender', models.CharField(max_length=10)),
                ('driver_phone_no', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region=None)),
                ('operator_name', models.CharField(max_length=100)),
                ('operator_gender', models.CharField(max_length=10)),
                ('operator_email', models.EmailField(max_length=254)),
                ('operator_phone_no', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region=None)),
                ('bus_start_timing', models.TimeField()),
                ('bus_start_from_school', models.TimeField()),
            ],
        ),
    ]