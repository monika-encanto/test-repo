# Generated by Django 4.2.10 on 2024-07-31 13:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0078_alter_classeventimage_event_image_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacheruser',
            name='fcm_token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]