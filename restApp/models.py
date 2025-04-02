from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import random

class CustomUser(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True, unique= True)
    address = models.TextField(blank=True, null=True)
    code = models.IntegerField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    dob = models.DateField(null=True, blank=True)   
    phone_token= models.CharField(null=True, blank=True, max_length=255) 

    def __str__(self):
        return self.username

class UserAccount(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='account')
    account_number = models.CharField(max_length=20, unique=True)
    account_type = models.CharField(max_length=50)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username}'s Account"

class PaymentMethod(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payment_methods')
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_expiry = models.DateField(blank=True, null=True)  # Format MM/YY
    billing_address = models.TextField(blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_account_number = models.CharField(max_length=20, blank=True, null=True)
    routing_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Payment Method"

class NfcData(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='nfc_data', null=True, blank=True)
    nfc_id = models.CharField(max_length=100)
    tech_list = models.JSONField()
    ndef_message = models.JSONField()
    max_size = models.IntegerField(null=True)
    is_writable = models.BooleanField(default=True)
    can_make_read_only = models.BooleanField(default=True)
    type = models.CharField(max_length=100)

    def __str__(self):
        return self.nfc_id

class Merchant(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='merchant_profile')
    business_name = models.CharField(max_length=255)

    def __str__(self):
        return self.business_name

class Transaction(models.Model):
    sender = models.ForeignKey(UserAccount, related_name='sent_transactions', on_delete=models.SET_NULL, null=True)
    recipient = models.ForeignKey(UserAccount, related_name='received_transactions', on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20)  # e.g., 'pending', 'completed'
    merchant = models.ForeignKey(Merchant, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'Transaction {self.transaction_id}'

# @receiver(post_save, sender=CustomUser)
# def create_user_account(sender, instance, created, **kwargs):
#     if created:
#         UserAccount.objects.create(
#             user=instance,
#             account_number=generate_account_number(),
#             account_type='Checking',  # Default account type
#         )

def generate_account_number():
    while True:
        account_number = str(random.randint(1000000000, 9999999999))
        if not UserAccount.objects.filter(account_number=account_number).exists():
            return account_number

CARD_TYPES = (
    ('Credit','Credit'),
    ('Debit','Debit'),
)

CARD_STATUS = (
    ('active','active'),
    ('inactive','inactive'),
    ('blocked','blocked'),
)

class NFCCARD(models.Model):
    serial_number = models.CharField(max_length=255)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,  null=True, blank=True, related_name='cards')
    card_number_last4 = models.CharField(max_length=4,  null=True, blank=True)  # Store only last 4 digits
    expiration_date = models.DateField(null=True, blank=True)
    card_type = models.CharField(max_length=10, null=True, blank=True, choices=CARD_TYPES)  # e.g., 'debit', 'credit'
    card_status = models.CharField(max_length=100, null=True, blank=True,choices=CARD_STATUS)  # e.g., 'active', 'inactive', 'blocked'
    card_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)


class FriendRequest(models.Model):
    
    sender = models.ForeignKey(CustomUser, related_name='sent_requests', on_delete=models.CASCADE)
    receiver = models.ForeignKey(CustomUser, related_name='received_requests', on_delete=models.CASCADE)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created = models.DateTimeField(auto_now_add=True)
    req_id = models.CharField(max_length=100, null=True, blank=True)

    

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})"




class TransactionEss(models.Model):
    STATUS_CHOICES = [
        ('SUCCESSFUL', 'Successful'),
        ('PENDING', 'Pending'),
        ('FAILED', 'Failed'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,  null=True, blank=True, related_name='user_transation')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    code = models.CharField(max_length=100)
    currency = models.CharField(max_length=10)
    description = models.TextField()
    external_reference = models.CharField(max_length=255, blank=True, null=True)
    external_user = models.CharField(max_length=255, blank=True, null=True)
    operator = models.CharField(max_length=100)
    operator_reference = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    reason = models.TextField(blank=True, null=True)
    reference = models.UUIDField()  # Assuming this is a UUID
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.amount} {self.currency} - {self.status}"
    
class Store(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='stores')
    name = models.CharField(max_length=20)
    location = models.CharField(max_length=30)
    timestamp = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name

class StoreTransaction(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='storepayment')
    store = models.OneToOneField(Store, on_delete=models.CASCADE)
    amount = models.CharField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)