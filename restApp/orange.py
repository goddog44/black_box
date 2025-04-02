# payments/orange.py

import requests
from django.conf import settings

def get_orange_money_token():
    url = "https://api.orange.com/oauth/v2/token"
    headers = {
        'Authorization': f'Basic {settings.ORANGE_CLIENT_ID}:{settings.ORANGE_CLIENT_SECRET}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, data=data, headers=headers)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(response.status_code, response.text)
        raise Exception('Failed to obtain access token')
    
# payments/orange.py

def initiate_payment(amount, currency, order_id, return_url, cancel_url, notification_url):
    access_token = get_orange_money_token()
    url = 'https://api.orange.com/orange-money-webpay/cm/v1/webpayment'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    body = {
        "merchant_key": settings.ORANGE_API_KEY,
        "amount": str(amount),
        "currency": currency,
        "order_id": order_id,
        "return_url": return_url,
        "cancel_url": cancel_url,
        "notification_url": notification_url,
        "lang": "en",
        # Additional optional fields
    }
    response = requests.post(url, json=body, headers=headers)
    if response.status_code == 201:
        return response.json()  # Contains payment URL and payload
    else:
        print(response.status_code, response.text)
        raise Exception('Payment initiation failed')