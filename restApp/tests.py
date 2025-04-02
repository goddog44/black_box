from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import *
from .serializer import *
from rest_framework_simplejwt.tokens import RefreshToken

# Get the custom user model
User = get_user_model()


# ----- View Tests -----
class NexusPayTestCase(APITestCase):

    def setUp(self):
        # Create users for testing
        self.user1 = CustomUser.objects.create_user(username="user1", password="password1")
        self.user2 = CustomUser.objects.create_user(username="user2", password="password2")

        # Create an authenticated client for user1
        self.client = APIClient()

        # Generate JWT tokens for user1
        self.refresh = RefreshToken.for_user(self.user1)
        self.access_token = str(self.refresh.access_token)

        # Add token to the APIClient's header
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

    def test_signup(self):
        url = reverse('signup')
        data = {
            "username": "new_user",
            "password": "new_password",
            "email": "new_user@example.com",
            "code": "1234"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_signup_invalid_data(self):
        url = reverse('signup')
        data = {
            "username": "",  # Invalid empty username
            "password": "short"  # Example of a weak password
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        url = reverse('login')
        data = {
            "username": "user1",
            "password": "password1"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        url = reverse('login')
        data = {
            "username": "user1",
            "password": "wrong_password"  # Invalid password
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout(self):
        url = reverse('logout')
        data = {
            "refresh": str(self.refresh)
        }
        response = self.client.post('/logout/', data)
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_user_profile(self):
        url = reverse('user_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user1.username)

    def test_mtn_mobile_money_payment(self):
        url = reverse('mtn_payment')
        data = {
            "amount": 100,
            "mobile_number": "655613839"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mtn_mobile_money_payment_failure(self):
        url = reverse('mtn_payment')
        data = {
            "amount": 100,
            "mobile_number": ""  # Missing mobile number
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_friend_request(self):
        url = reverse('send_user_friend_request', args=[self.user2.phone_token])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_accept_friend_request(self):
        friend_request = FriendRequest.objects.create(sender=self.user1, receiver=self.user2)
        url = reverse('accept_friend_request', args=[friend_request_id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_decline_friend_request(self):
        friend_request = FriendRequest.objects.create(sender=self.user1, receiver=self.user2)
        url = reverse('refuse_friend_request', args=[friend_request.id, self.user2.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_merchant_payment(self):
        url = reverse('merchant_payment')
        data = {
            "nfc_id": "123456",
            "amount": "50.00"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ----- Serializer Tests -----
class SerializerTestCase(APITestCase):
    
    def setUp(self):
        # Create dummy data for testing
        self.user = CustomUser.objects.create_user(
            username="testuser", 
            email="testuser@example.com", 
            password="password123",
            first_name="Test",
            last_name="User",
            phone="1234567890",
            address="123 Test Street"
        )
    
    def test_signup_serializer(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'User',
            'phone': '0987654321',
            'address': '456 Another St',
            'code': '1234',
            'dob': '1990-01-01',
            'phone_token': 'some_token'
        }
        serializer = SignupSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, 'newuser')
        self.assertTrue(user.check_password('password123'))  # Password hashing is correct

    def test_nfc_data_serializer(self):
        nfc_data = NfcData.objects.create(
            nfc_id="12345",
            tech_list="ISO14443",
            ndef_message="Sample NFC Message",
            max_size=512,
            is_writable=True,
            can_make_read_only=False,
            type="Type A"
        )
        serializer = NfcDataSerializer(nfc_data)
        self.assertEqual(serializer.data['nfc_id'], "12345")
        self.assertEqual(serializer.data['tech_list'], "ISO14443")
    
    def test_custom_user_serializer(self):
        serializer = CustomUserSerializer(self.user)
        self.assertEqual(serializer.data['username'], 'testuser')
        self.assertEqual(serializer.data['email'], 'testuser@example.com')
        self.assertEqual(serializer.data['full_name'], 'Test User')
    
    def test_friend_serializer(self):
        friend_request = FriendRequest.objects.create(sender=self.user, receiver=self.user)
        serializer = friendSerializer(friend_request)
        self.assertEqual(serializer.data['sender']['username'], self.user.username)
        self.assertEqual(serializer.data['receiver']['username'], self.user.username)