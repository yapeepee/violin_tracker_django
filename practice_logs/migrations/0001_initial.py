# Generated by Django 5.2 on 2025-05-29 06:06

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Practicelog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_name', models.CharField(max_length=100)),
                ('piece', models.CharField(max_length=200)),
                ('minutes', models.PositiveIntegerField()),
                ('rating', models.PositiveIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
                ('date', models.DateField(auto_now_add=True)),
            ],
        ),
    ]
