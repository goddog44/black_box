from django.contrib import admin
from .models import *

# Custom admin for CustomUser model
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = [field.name for field in CustomUser._meta.fields if field.name != 'password']
    search_fields = ['username', 'email']  # Optional: Add search by username or email

@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = [field.name for field in UserAccount._meta.fields if field.name != 'password']
    search_fields = ['account_number', 'user__username']
    list_filter = ['account_type', 'user__is_active']
    ordering = ['-balance']
    list_per_page = 20

    
# Custom admin for PaymentMethod model
@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = [field.name for field in PaymentMethod._meta.fields]  # Display all fields
    search_fields = ['user__username', 'card_last4']  # Optional: Add search by username or card last 4 digits

# Custom admin for NfcData model
@admin.register(NfcData)
class NfcDataAdmin(admin.ModelAdmin):
    list_display = [field.name for field in NfcData._meta.fields]  # Display all fields
    search_fields = ['user__username', 'nfc_tag']  # Optional: Add search by username or NFC tag

# Custom admin for Merchant model
@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Merchant._meta.fields]  # Display all fields
    search_fields = ['name', 'merchant_id']  # Optional: Add search by name or merchant ID

# Custom admin for Transaction model
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Transaction._meta.fields]  # Display all fields
    search_fields = ['transaction_id', 'user__username', 'merchant__name']  # Optional: Add search by transaction ID, username, or merchant name


@admin.register(NFCCARD)
class NFCCARDAdmin(admin.ModelAdmin):
    list_display = [field.name for field in NFCCARD._meta.fields]  # Display all fields
@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = [field.name for field in FriendRequest._meta.fields]  # Display all fields
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Store._meta.fields] 

@admin.register(StoreTransaction)
class StoreTransactionAdmin(admin.ModelAdmin):
    list_display = [field.name for field in StoreTransaction._meta.fields]