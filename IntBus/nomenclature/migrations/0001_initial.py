# Generated by Django 5.2 on 2025-04-07 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LSI',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Nomenclature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abbreviation', models.CharField(max_length=100)),
                ('short_name', models.CharField(max_length=255)),
                ('full_name', models.CharField(max_length=255)),
                ('internal_code', models.CharField(max_length=100)),
                ('cipher', models.CharField(max_length=100)),
                ('ekps_code', models.CharField(max_length=100)),
                ('kvt_code', models.CharField(max_length=100)),
                ('drawing_number', models.CharField(max_length=100)),
                ('type_of_nomenclature', models.CharField(max_length=100)),
            ],
        ),
    ]
