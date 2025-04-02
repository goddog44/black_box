from django.shortcuts import render, get_object_or_404
from . models import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializer import * 
from django.db.models.signals import post_save
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.utils.crypto import get_random_string
from .mtn import request_to_pay, check_transaction_status
import time
from rest_framework import viewsets, permissions
from django.db import transaction
from decimal import Decimal, InvalidOperation
import uuid

class LoginView(APIView):
    serializer_class = ReactSerializer
    def post(self, request):
        serializer = ReactSerializer(data=request.data)
        if serializer.is_valid():
            if serializer.is_valid():
                print(serializer.data)
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            if user is not None:
                # Generate tokens
                refresh = RefreshToken.for_user(user)
                
                # Return the tokens in the response
                return Response({
                    'message': 'Login successful',
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            else:
                # If authentication fails, return an error response
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            # If serializer validation fails, return the errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class SignupView(APIView):
    # serializer_class = SignupSerializer
    @transaction.atomic
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save()

            UserAccount(
            user=data,
            account_number=generate_account_number(),
            account_type='Checking',  # or other default type
        ).save()
            return Response({'message': 'User created successfully'},
                            status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def nfc_data_view(request):
    if request.method == 'POST':
        serializer = NfcDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mtn_mobile_money_payment(request):
    amount = request.data.get('amount')
    currency = 'EUR'  # or 'XAF' depending on the region
    mobile_number = request.data.get('mobile_number')  # Customer's mobile number
    payer_message = "Payment for goods"
    payee_note = "Thank you"
    external_id = str(uuid.uuid4())
    
    try:
        reference_id = request_to_pay(amount, currency, external_id, payer_message, payee_note, mobile_number)
        # Wait for a few seconds before checking the status
        time.sleep(5)
        transaction_status = check_transaction_status(reference_id)
        if transaction_status['status'] == 'SUCCESSFUL':
            # Process the payment in your system
            return Response({'message': 'Payment successful'}, status=200)
        else:
            return Response({'error': 'Payment failed'}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def orange_money_payment(request):
    amount = request.data.get('amount')
    currency = 'XAF'  # Or appropriate currency
    order_id = str(uuid.uuid4())
    return_url = 'https://your-app.com/payment-success/'
    cancel_url = 'https://your-app.com/payment-cancel/'
    notification_url = 'https://your-backend.com/api/orange-money-notification/'
    
    try:
        payment_response = initiate_payment(amount, currency, order_id, return_url, cancel_url, notification_url)
        payment_url = payment_response.get('payment_url')
        return Response({'payment_url': payment_url}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# payments/views.py
@api_view(['POST'])
def orange_money_notification(request):
    data = request.data
    # Verify the notification (signature, order_id, etc.)
    # Update your records accordingly
    return Response(status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure merchants are authenticated
def merchant_payment(request):
    nfc_id = request.data.get('nfc_id')
    amount = request.data.get('amount')
    if not nfc_id or not amount:
        return Response({'error': 'Missing required fields.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        amount = Decimal(amount)
    except InvalidOperation:
        return Response({'error': 'Invalid amount.'}, status=status.HTTP_400_BAD_REQUEST)

    # Find the customer account based on the NFC card
    try:
        nfc_card = NfcCard.objects.get(card_id=nfc_id)
        customer_account = nfc_card.user_account
    except NfcCard.DoesNotExist:
        return Response({'error': 'NFC card not registered.'}, status=status.HTTP_400_BAD_REQUEST)

    merchant_account = UserAccount.objects.get(user=request.user)

    # Security checks
    if customer_account.balance < amount:
        return Response({'error': 'Customer has insufficient funds.'}, status=status.HTTP_400_BAD_REQUEST)

    # Create the transaction
    transaction = Transaction.objects.create(
        sender=customer_account,
        recipient=merchant_account,
        amount=amount,
        transaction_id=get_random_string(12),
        status='completed',
        merchant=request.user.merchant,  # assuming 'user' has a 'merchant' related object
    )

    # Update balances
    customer_account.balance -= amount
    customer_account.save()

    merchant_account.balance += amount
    merchant_account.save()

    transaction_serializer = TransactionSerializer(transaction)

    return Response({'message': 'Payment successful.', 'transaction': transaction_serializer.data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def nfc_payment(request):
    tag_data = request.data.get('tag_data')
    nfc_id = tag_data.get('id') if tag_data else None

    if not nfc_id:
        return Response({'error': 'Invalid NFC data.'}, status=400)

    try:
        nfc_card = NfcData.objects.get(card_id=nfc_id)
        sender_account = nfc_card.user_account
    except NfcData.DoesNotExist:
        return Response({'error': 'NFC card not registered.'}, status=400)

    recipient_account = UserAccount.objects.get(user=request.user)

    # Assume amount is included in the request or predetermined
    amount = request.data.get('amount', 10.00)  # Replace with actual logic

    if sender_account.balance < amount:
        return Response({'error': 'Insufficient funds.'}, status=400)

    # Create transaction
    transaction = Transaction.objects.create(
        sender=sender_account,
        recipient=recipient_account,
        amount=amount,
        transaction_id=get_random_string(12),
        status='completed',
    )

    # Update balances
    sender_account.balance -= amount
    sender_account.save()
    recipient_account.balance += amount
    recipient_account.save()

    return Response({'message': 'Payment successful.'}, status=200)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    serializer = CustomUserSerializer(user, context={'request': request})
    user_card = NFCCARD.objects.filter(user = user)
    s2 = NFCCARDSerializer(user_card, many=True)
    return Response(serializer.data)
     
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def user_cards(request):
     cards = request.NFCCARD
     nfc_card_data = NFCCARDSerializer(cards, context={'request': request})
     return Response(nfc_card_data)



# @receiver(post_save, sender=CustomUser)
# def create_user_account(sender, instance, created, **kwargs):
#     if created:
#         # Create a UserAccount for the new user
#         UserAccount.objects.create(
#             user=instance,
#             account_number=generate_account_number(),
#             account_type='Checking',  # or other default type
#         )
        # If the user is a merchant, create a Merchant profile
        # Assuming you have a way to determine if the user is a merchant
        # if instance.is_merchant:
        #     Merchant.objects.create(user=instance, business_name=instance.business_name)


def generate_account_number():
    # Generate a unique 10-digit account number
    while True:
        account_number = str(random.randint(1000000000, 9999999999))
        if not UserAccount.objects.filter(account_number=account_number).exists():
            return account_number

def generate_transaction_id():
    # Generate a unique 10-digit account number
    while True:
        account_number = str(random.randint(1000000000, 9999999999))
        if not Transactions.objects.filter(transaction_id=transaction_id).exists():
            return transaction_id


# @receiver(post_save, sender=CustomUser)
# def save_user_account(sender, instance, **kwargs):
#     if hasattr(instance, 'account'):
#         instance.account.save()
    
@api_view(['POST'])
def process(request):
    card = request.GET.get('card_id')
    if not card:
        return HttpResponse("No card ID provided")

    card = NFCCARD.objects.create(serial_number = card)
    return Response(card.serial_number)

@api_view(['GET'])
def check_user_by_phone_number(request, phone_number):
    user = get_object_or_404(CustomUser, phone = phone_number)
    data = {
        'id': user.id,
        'token': user.phone_token,
    }
    return Response(data)



from .dev import send_push_notification
import json
@api_view(['POST'])
# @permission_classes([IsAuthenticated])
@transaction.atomic
def Send_user_friend_request(request, phone_token):
    print('fh')
    try:
        user = request.user
        data = {
           "friend": json.dumps(CustomUserSerializer(user).data),
            'type':'freind'
        }   
        message = f' {user.username} Sent you a freind request'
        print(user.username)
        res = send_push_notification(phone_token,'Friend Request',message,data)
        if res:
            return Response({'msg':'sent'})
        else:
            print(res)
            return Response({'msg':'err'},status=400)
    except Exception as e :
        print(e)
        return Response({'msg':'err'},status=400)

from .models import FriendRequest

@api_view(['POST'])
def accept_friend_request(request, request_id, friend_id):
    try:
        user = get_object_or_404(CustomUser, pk = friend_id)
        connected_user = request.user
        

        print('User' , user)
        print('User' , connected_user)
        try:
            friend_request = FriendRequest.objects.get(sender=user, receiver=connected_user)
            friend_request.status = 'accepted'
            friend_request.save()

            return Response({'msg': 'Friend request accepted'})
        except Exception as e:
            print(e)
            return Response({'msg': 'Error accepting friend request'}, status=404)
        # # friend_request = get_object_or_404(FriendRequest, status='accepted')
        # # friend_request.status = 'accepted'
        # # friend_request.save()
        # print(request.headers)
        # friend = FriendRequest()


        # friend.sender = user
        # friend.receiver = connected_user
        # friend.status = 'accepted'
        # friend.save()
        
        # Optionally, you can add logic to add the users as friends in your system
        # For example, create a Friendship model to store accepted friendships
        # Friendship.objects.create(user_1=friend_request.sender, user_2=friend_request.receiver)

        # return Response({'msg': 'Friend request accepted'})
    except Exception as e:
        print(e)
        return Response({'msg': 'Error accepting friend request'}, status=400)
    
@api_view(['POST'])
def refuse_friend_request(request, request_id, friend_id):
    try:
        user = get_object_or_404(CustomUser, pk = friend_id)
        connected_user = request.user
        

        print('User' , user)
        print('User' , connected_user)
        try:
            friend_request = FriendRequest.objects.get(sender=user, receiver=connected_user)
            friend_request.status = 'declined'
            friend_request.save()

            return Response({'msg': 'Friend request declined'})
        except Exception as e:
            print(e)
            return Response({'msg': 'Error decline friend request'}, status=404)
        # # friend_request = get_object_or_404(FriendRequest, status='accepted')
        # # friend_request.status = 'accepted'
        # # friend_request.save()
        # print(request.headers)
        # friend = FriendRequest()


        # friend.sender = user
        # friend.receiver = connected_user
        # friend.status = 'accepted'
        # friend.save()
        
        # Optionally, you can add logic to add the users as friends in your system
        # For example, create a Friendship model to store accepted friendships
        # Friendship.objects.create(user_1=friend_request.sender, user_2=friend_request.receiver)

        # return Response({'msg': 'Friend request accepted'})
    except Exception as e:
        print(e)
        return Response({'msg': 'Error declining friend request'}, status=400)
    
from .models import FriendRequest

@api_view(['POST'])
# @permission_classes([IsAuthenticated])
@transaction.atomic
def Send_user_friend_request(request, phone_token):
    try:
        user = request.user
        data = {
            "friend": json.dumps(CustomUserSerializer(user).data),
            'type': 'friend'
        }
        print('DFR ',user)
        receiver = CustomUser.objects.filter(phone_token=phone_token).first()
        print('DFR ',receiver)
        # Create a friend request
        message = f'{user.username} sent you a friend request'
        print(user.username)
        res = send_push_notification(phone_token, 'Friend Request', message, data)
        friend_request, created = FriendRequest.objects.get_or_create(sender=user, receiver=receiver)

        if not created:
            print('Here')
            return Response({'msg': 'Friend request already exists'}, status=400)

        # Send a push notification
     
       

        if res:
            return Response({'msg': 'sent'})
        else:
            return Response({'msg': 'err'}, status=400)
    except Exception as e:
        print(e)
        return Response({'msg': 'err'}, status=400)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_friend(request):
    friend1 = FriendRequest.objects.filter(sender = request.user)
    friend2= FriendRequest.objects.filter(receiver = request.user)
    friends = friend1 
    serializers = friendSerializer(friends, many=True)
    serializers2 = friendSerializer(friend2, many=True)
    data = serializers2.data + serializers.data
    return Response({'me':request.user.id,'freinds':data})



from rest_framework import viewsets

class TransactionViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing transaction instances.
    """
    queryset = TransactionEss.objects.all()
    serializer_class = TransactionSerializerEss
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # Ajouter l'utilisateur connecté à la transaction
        data = request.data.copy()
        data2 = request.data.copy()
        data['user'] = 3  # Associer l'ID de l'utilisateur à la transaction
        # data['user'] = request.user.id  # Associer l'ID de l'utilisateur à la transaction
        print(request.data)

        
        try:
            # Tenter de créer la transaction avec les données modifiées
            if data2['status'] == "SUCCESSFUL":
                user = request.user
                account = UserAccount.objects.get(user__id = 3)
                account.balance = account.balance + data2['amount']
                account.save()
            response = super().create(request, *args, **kwargs)
            return response  # Retourner la réponse de la méthode parent

        except Exception as e:
            # Gérer les exceptions et imprimer l'erreur
            print("Error creating transaction:", str(e))
            return Response({"error": "Failed to create transaction", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['post'])
@permission_classes([IsAuthenticated])
def rechargeCard(request):
    data = request.GET.get('amount')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_in_store(request):
    return Response("success")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def display_in_store(request):
    data = Store.objects.all()
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_Store_transaction_for_user(request):
    transactions = StoreTransaction.objects.filter(user=request.user)
    serializer = StoreTransactionSerializer(transactions, many=True)
    data = serializer.data
    return Response({'StoreTransaction':data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_money_from_my_friend(request):
    try:
        id = request.data['id']
        user = CustomUser.objects.get(id=id)
        print(user)
        amount = request.data['amount']

        print(amount)

        data = {
        #    "friend": json.dumps(CustomUserSerializer(user).data),
            'type':'money',
            'amount':amount,
            'user':request.user.username,
            'id':str(request.user.id)
        }  

        res = send_push_notification(user.phone_token, 'Money Request', f'{request.user} ask you a money {amount} Fcfa', data)

        return Response({'msg':'Request Sent'})
    except:
        return Response(status = 400)
   
    return Response()




@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def recharge_card(request, card_id):
   
    card = NFCCARD.objects.get(pk = card_id)
    amount = 0
    try:
        amount = request.data['amount']
    except:
        return Response({'error':'Amount is needed'}, status = 400)
    
    user = card.user
    account = UserAccount.objects.get(user = user)

    if int(account.balance) >= int(amount):
        account.balance = int(account.balance) - int(amount)
        card.card_balance = int(card.card_balance) + int(amount)

        account.save()
        card.save()
        return Response({'msg':'Save successfully'})
    
    else:
        return Response({'error':'Insufficient Balance' }, status = 400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def approuve_money(request, f_id, amount):
    from_ = request.user
    to = CustomUser.objects.get(pk = f_id)

    from_account = UserAccount.objects.get(user = from_)
    to_account = UserAccount.objects.get(user = to)


    from_account.balance = int(from_account.balance) - int(amount)
    to_account.balance = int(to_account.balance) + int(amount)

    to_account.save()
    from_account.save()
    data = {
        #    "friend": json.dumps(CustomUserSerializer(user).data),
            'type':'money',
            'amount':amount,
            'user':request.user.username,
            'id:':str(request.user.id)
        }  

    res = send_push_notification(to.phone_token, 'Money Request validated', f'{request.user} has validate your money request', {})

    return Response(status=200)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def pay_with_nfc(request, card_id ):
   
    card = NFCCARD.objects.filter(serial_number = card_id).first()
    amount = 0
    try:
        amount = request.data['amount']
    except:
        return Response({'error':'Amount is needed'}, status = 400)
    
    user = card.user
    account = UserAccount.objects.get(user = user)

    if int(card.card_balance) >= int(amount):
        account.balance = int(account.balance) - int(amount)
        card.card_balance = int(card.card_balance) + int(amount)

        account.save()
        card.save()
        return Response({'msg':'Save successfully'})
    
    else:
        return Response({'error':'Insufficient Balance' }, status = 400)




from .models import Store as DEV
@api_view(['POST'])
@transaction.atomic
def pay_with_nfc2(request):
    
    card_id = request.data['id_card']
    card = NFCCARD.objects.filter(serial_number = card_id).first()
    amount = 0
    amount = request.data['money']
    store = DEV.objects.get(pk = 2)
    user = CustomUser.objects.get(id = store.user.id)
    try:
        amount = request.data['money']
    except:
        return Response({'error':'Amount is needed'}, status = 400)
    

    account = UserAccount.objects.get(user = user)

    if int(card.card_balance) >= int(amount):
        card.card_balance = int(card.card_balance) - int(amount)
        account.balance = int(account.balance) + int(amount)

        account.save()
        card.save()
        return Response({'msg':'Save successfully'})
    
    else:
        return Response({'error':'Insufficient Balance' }, status = 400)