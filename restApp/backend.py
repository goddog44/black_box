from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import CustomUser

class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = CustomUser.objects.get(Q(email=username) | Q(phone=username))
            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            return None