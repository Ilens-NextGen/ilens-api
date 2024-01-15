from rest_framework.response import Response
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_204_NO_CONTENT,
)
from rest_framework.generics import CreateAPIView, GenericAPIView
from .models import BLToken
from .serializers import (
    UserCreateSerializer,
    UserSerializer,
    RequestSerializer,
    PasswordResetSerializer,
    UserManageSerializer,
    EmptySerializer,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from .backends import CustomJWTAuthentication
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenBlacklistView,
    TokenRefreshView,
)
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from .signals import verification_token_created, pwd_reset_token_created
from ilens.core.encrypt import generate_otps, verify_otps

User = get_user_model()


class LoginView(TokenObtainPairView):
    pass


class SignupView(CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user_serializer = UserSerializer(user)
        token = generate_otps(user.id, "vyf")
        verification_token_created.send(
            sender=self.__class__,
            instance=self,
            verification_token=token,
            user_email=user.email,
        )
        return Response(user_serializer.data, status=HTTP_201_CREATED)


class LogoutView(TokenBlacklistView):
    permission_classes = [IsAuthenticated]  # type: ignore[assignment]
    authentication_classes = [CustomJWTAuthentication]  # type: ignore[assignment]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        header = request.headers.get("Authorization")
        token = header.split(" ")[1]
        BLToken.objects.create(key=token, user=request.user)
        return response


class RefreshTokenView(TokenRefreshView):
    pass


class PasswordResetRequestView(GenericAPIView):
    serializer_class = RequestSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        user = User.objects.filter(email=email).first()
        if user:
            token = generate_otps(user.id, "pwd")
            pwd_reset_token_created.send(
                sender=self.__class__, instance=self, token=token, user_email=user.email
            )
            return Response(
                {"message": "A reset_password_token has been sent to your email"},
                status=HTTP_200_OK,
            )
        return Response(
            {"message": "There's no user with this email"}, status=HTTP_400_BAD_REQUEST
        )


@receiver(pwd_reset_token_created)
def password_reset_token_created(sender, instance, token, user_email, *args, **kwargs):
    email_plaintext_message = "{}/{}".format(
        "http://localhost:8000/reset-password", token
    )

    email = EmailMultiAlternatives(
        "Password Reset for {title}".format(title="MadChatter"),
        email_plaintext_message,
        "noreply@somehost.local",
        [user_email],
    )
    email.send()


class PasswordResetConfirmView(GenericAPIView):
    serializer_class = PasswordResetSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        token = kwargs.get("token", "")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        pwd = serializer.validated_data.get("password")
        _pwd = serializer.validated_data.get("confirm_password")

        user, status = verify_otps(token, "pwd")

        if status == 400:
            return Response(
                {"status": "invalid or expired token"}, status=HTTP_400_BAD_REQUEST
            )
        if status == 400:
            return Response(
                {"status": "User does not exist. May have been deleted"},
                status=HTTP_404_NOT_FOUND,
            )
        if pwd != _pwd:
            return Response(
                {"status": "passwords do not match"}, status=HTTP_400_BAD_REQUEST
            )
        user.set_password(pwd)
        user.save()
        return Response({"status": "success"}, status=HTTP_200_OK)


class RequestVerificationView(GenericAPIView):
    serializer_class = RequestSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        user = User.objects.filter(email=email).first()
        if user:
            token = generate_otps(user.id, "vyf")
            verification_token_created.send(
                sender=self.__class__,
                instance=self,
                verification_token=token,
                user_email=user.email,
            )
            return Response(
                {"message": "A verification_token has been sent to your email"},
                status=HTTP_200_OK,
            )
        return Response(
            {"message": "There's no user with this email"}, status=HTTP_400_BAD_REQUEST
        )


@receiver(verification_token_created)
def verification_token_mail(
    sender, instance, verification_token, user_email, *args, **kwargs
):
    email_plaintext_message = "{}/{}".format(
        "http://localhost:8000/verify", verification_token
    )

    email = EmailMultiAlternatives(
        "Verification for {title}".format(title="MadChatter"),
        email_plaintext_message,
        "noreply@somehost.local",
        [user_email],
    )
    email.send()


class VerificationConfirmView(GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = EmptySerializer

    def get(self, request, *args, **kwargs):
        token = kwargs.get("token", "")
        user, status = verify_otps(token, "vyf")
        if status == 400:
            return Response(
                {"status": "invalid or expired token"}, status=HTTP_400_BAD_REQUEST
            )
        if not user:
            return Response(
                {"status": "User does not exist. May have been deleted"},
                status=HTTP_404_NOT_FOUND,
            )
        user.is_verified = True
        user.save()
        return Response({"status": "success"}, status=HTTP_200_OK)


class UserView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserManageSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
        return Response(self.serializer_class(user).data, status=HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.delete()
        return Response(
            {"message": f"Successfully deleted USER - {kwargs['id']}"},
            status=HTTP_204_NO_CONTENT,
        )
