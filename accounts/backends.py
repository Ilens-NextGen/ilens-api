from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import BLToken

User = get_user_model()


class CustomJWTAuthentication(JWTAuthentication):
    """Custom JWT authentication, same as the one provided by rest_framework simplejwt except
    that it checks for any blacklisted access token first"""

    def authenticate(self, request):
        """Checks if the token was recently blacklisted"""
        result = super().authenticate(request)
        header = self.get_header(request)
        if result:
            token = self.get_raw_token(header).decode("utf-8")
            if BLToken.objects.filter(key=token).exists():
                raise AuthenticationFailed("Token is blacklisted")
        return result
