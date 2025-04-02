# payments/mtn.py

import requests
from django.conf import settings

def generate_api_user():
    url = "https://sandbox.momodeveloper.mtn.com/v1_0/apiuser"
    headers = {
        'Ocp-Apim-Subscription-Key': settings.MTN_SUBSCRIPTION_KEY,
        'Content-Type': 'application/json',
    }
    body = {
        "providerCallbackHost": "https://your-callback-url.com/"
    }
    response = requests.post(url, json=body, headers=headers)
    print(response.status_code, response.text)

    # payments/mtn.py

def get_access_token():
    url = "https://sandbox.momodeveloper.mtn.com/collection/token/"
    headers = {
        'Authorization': f'Basic {settings.MTN_API_USER}:{settings.MTN_API_KEY}',
        'Ocp-Apim-Subscription-Key': settings.MTN_SUBSCRIPTION_KEY,
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception('Failed to obtain access token')
    

# payments/mtn.py

import uuid

def request_to_pay(amount, currency, external_id, payer_message, payee_note, mobile_number):
    access_token = get_access_token()
    url = "https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Reference-Id': str(uuid.uuid4()),  # Unique transaction ID
        'X-Target-Environment': 'sandbox',
        'Ocp-Apim-Subscription-Key': settings.MTN_SUBSCRIPTION_KEY,
        'Content-Type': 'application/json',
    }
    body = {
        "amount": str(amount),
        "currency": currency,
        "externalId": external_id,
        "payer": {
            "partyIdType": "MSISDN",
            "partyId": mobile_number  # In international format without the '+'
        },
        "payerMessage": payer_message,
        "payeeNote": payee_note
    }
    response = requests.post(url, json=body, headers=headers)
    if response.status_code == 202:
        return headers['X-Reference-Id']  # Use this to check the transaction status
    else:
        print(response.status_code, response.text)
        raise Exception('Request to pay failed')
    
# payments/mtn.py

def check_transaction_status(reference_id):
    access_token = get_access_token()
    url = f"https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay/{reference_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Target-Environment': 'sandbox',
        'Ocp-Apim-Subscription-Key': settings.MTN_SUBSCRIPTION_KEY,
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(response.status_code, response.text)
        raise Exception('Failed to get transaction status')