# Generated by Django 5.0.7 on 2024-09-26 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restApp', '0003_nfccard_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='nfccard',
            name='card_number_last4',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='nfccard',
            name='card_status',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='nfccard',
            name='card_type',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='nfccard',
            name='expiration_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
