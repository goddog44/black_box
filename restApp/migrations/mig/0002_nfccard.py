# Generated by Django 5.0.7 on 2024-09-26 05:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NFCCARD',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serial_number', models.CharField(max_length=255)),
            ],
        ),
    ]
