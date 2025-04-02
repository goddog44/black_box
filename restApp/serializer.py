from rest_framework import serializers
from .models import *

class ReactSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'username', 
            'email', 
            'password', 
            'first_name', 
            'last_name', 
            'phone', 
            'address', 
            'code',
            'full_name',
            'dob',
            'phone_token',
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            address=validated_data.get('address', ''),
            code=validated_data.get('code', ''),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class NfcDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = NfcData
        fields = [
            'nfc_id', 
            'tech_list', 
            'ndef_message', 
            'max_size', 
            'is_writable', 
            'can_make_read_only', 
            'type'
        ]

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class PaymentMethodSerializer(serializers.ModelSerializer):
    bank_account_number = serializers.SerializerMethodField()
    routing_number = serializers.SerializerMethodField()

    class Meta:
        model = PaymentMethod
        fields = [
            'id',
            'card_last4',
            'card_expiry',
            'billing_address',
            'bank_name',
            'bank_account_number',
            'routing_number',
        ]

    def get_bank_account_number(self, obj):
        if obj.bank_account_number:
            return f"****{obj.bank_account_number[-4:]}"
        return None

    def get_routing_number(self, obj):
        if obj.routing_number:
            return f"****{obj.routing_number[-4:]}"
        return None

class UserAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = [
            'account_number',
            'account_type',
            'balance',
            'available_balance',
        ]
        
class NFCCARDSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFCCARD
        fields = '__all__' # You can also specify fields explicitly

class CustomUserSerializer(serializers.ModelSerializer):
    account = UserAccountSerializer(read_only=True)
    cards = NFCCARDSerializer(many=True, read_only=True)
    payment_methods = PaymentMethodSerializer(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'full_name',
            'phone',
            'address',
            'profile_picture',
            'account',
            'cards',
            'payment_methods',
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_profile_picture(self, obj):
        request = self.context.get('request')
        if obj.profile_picture and request:
            return request.build_absolute_uri(obj.profile_picture.url)
        return None
    
class friendSerializer(serializers.ModelSerializer):
    sender = CustomUserSerializer()
    receiver =CustomUserSerializer()
    class Meta:
        model = FriendRequest
        fields = '__all__'



class TransactionSerializerEss(serializers.ModelSerializer):
    class Meta:
        model = TransactionEss
        fields = '__all__'  # You can also specify fields explicitly if 

class Store(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__' # You can also specify fields explicitly

class StoreTransactionSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source = 'store.name')
    store_location = serializers.CharField(source = 'store.location')

    class Meta:
        model = StoreTransaction
        fields  = '__all__' # You can also specify