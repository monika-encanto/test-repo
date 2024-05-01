# Generated by Django 4.2.10 on 2024-04-30 07:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0047_studentuser_guardian_no'),
    ]

    operations = [
        migrations.AlterField(
            model_name='certificate',
            name='certificate_file',
            field=models.FileField(upload_to='certificate/'),
        ),
        migrations.AlterField(
            model_name='staffuser',
            name='image',
            field=models.ImageField(blank=True, upload_to='staff_images/'),
        ),
        migrations.AlterField(
            model_name='studentuser',
            name='image',
            field=models.ImageField(blank=True, upload_to='student_images/'),
        ),
        migrations.AlterField(
            model_name='teacheruser',
            name='image',
            field=models.ImageField(blank=True, upload_to='teacher_images/'),
        ),
    ]