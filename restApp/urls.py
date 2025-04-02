from django.urls import path 
from restApp.views import LoginView, SignupView, LogoutView
from . import views 

from django.urls import path, include
from rest_framework.routers import DefaultRouter


from .views import TransactionViewSet

# Create a router and register our ViewSets with it.
router = DefaultRouter()
router.register(r'transactions', TransactionViewSet)

urlpatterns = [
    path('login/',  LoginView.as_view(), name="login"),
    path('signup/', SignupView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('nfc/', views.nfc_data_view, name='nfc-data'),
    path('process/', views.process, name='process'),
    # path('receive-payment/', views.receive_payment, name='receive_payment'),
    path('mtn-payment/', views.mtn_mobile_money_payment, name='mtn_payment'),
    path('orange-money-payment/', views.orange_money_payment, name='orange_money_payment'),
    path('orange-money-notification/', views.orange_money_notification, name='orange_money_notification'),
    path('merchant-payment/', views.merchant_payment, name='merchant_payment'),
    path('nfc-payment/', views.nfc_payment, name='nfc_payment'),
    path('profile/', views.user_profile, name='user_profile'),
    path('check_user_by_phone_number/<str:phone_number>/', views.check_user_by_phone_number, name='check_user_by_phone_number'),
    path('Send_user_friend_request/<phone_token>/', views.Send_user_friend_request, name='send_user_friend_request'),
    path('refuse_friend_request/<request_id>/<friend_id>/', views.refuse_friend_request, name='refuse_friend_request'),
    path('accept_friend_request/<request_id>/<friend_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('get_friend/', views.get_friend, name='get_friend'),
    path('', include(router.urls)),
    path('display_in_store/', views.display_in_store, name="display_in_store"),
    path('save_in_store/', views.save_in_store, name="save_in_store"),
    path('get_all_Store_transaction_for_user/', views.get_all_Store_transaction_for_user, name='get_all_Store_transaction_for_user'),
    path('recharge_card/<card_id>/', views.recharge_card, name='recharge_card'),
    path('pay_with_nfc/<card_id>/', views.pay_with_nfc, name='pay_with_nfc'),
    path('pos/', views.pay_with_nfc2, name='pay_with_nfc2'),
    path('request_money_from_my_friend/', views.request_money_from_my_friend, name='request_money_from_my_friend'),
    path('approuve_money/<f_id>/<amount>/', views.approuve_money, name='approuve_money'),
]