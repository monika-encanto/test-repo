# Generated by Django 4.2.10 on 2024-03-16 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0009_addressdetails'),
    ]

    operations = [
        migrations.CreateModel(
            name='ErrorLogging',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('context', models.TextField(blank=True, null=True)),
                ('exception', models.TextField(blank=True, null=True)),
                ('traceback', models.TextField(blank=True, null=True)),
            ],
        ),
    ]
