from rest_framework.serializers import (
    ModelSerializer, EmailField,
    ValidationError, Serializer,
    CharField)
import  ilens.core.validators as v
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model

User = get_user_model()
class CustomAuthTokenSerializer(Serializer):
    email = EmailField()
    password = CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        if email and password:
            user = User.objects.filter(email=email).first()
            if user and user.check_password(password):
                attrs['user'] = user
                return attrs
            else:
                raise ValidationError('Unable to log in with provided credentials.')
        else:
            raise ValidationError('Must include "email" and "password".')

class UserCreateSerializer(ModelSerializer):
    email = EmailField()
    username = CharField(max_length=50, write_only=True)
    password = CharField(validators=[v.validate_password], write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'username']
        
    def create(self, validated_data):
        try:
            user = super().create(validated_data)
            user.set_password(validated_data['password'])
            user.save()
            return user
        except IntegrityError:
            raise ValidationError("A user with this email already exists")


class UserSerializer(ModelSerializer):
    
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'id',
                  'last_name', 'created_at']
        read_only_fields = ['id']
        
class UserManageSerializer(ModelSerializer):    
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'id',
                  'last_name', 'created_at',
                ]
        read_only_fields = ['id', 'created_at']

class RequestSerializer(Serializer):
    email = EmailField()

class PasswordResetSerializer(Serializer):
    password = CharField(validators=[v.validate_password])
    confirm_password = CharField(validators=[v.validate_password])

class EmptySerializer(Serializer):
    pass
