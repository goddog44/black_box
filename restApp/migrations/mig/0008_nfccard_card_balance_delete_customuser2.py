# Generated by Django 5.0.7 on 2024-09-29 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restApp', '0007_alter_paymentmethod_card_expiry'),
    ]

    operations = [
        migrations.AddField(
            model_name='nfccard',
            name='card_balance',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=12),
        ),
        migrations.DeleteModel(
            name='CustomUser2',
        ),
    ]
