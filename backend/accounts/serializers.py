from rest_framework import serializers
from .models import User

class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField()
    password = serializers.CharField(min_length=8)
    role = serializers.ChoiceField(choices=["INTERN", "SUPERVISOR"])

class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "employee_id", "department", "supervisor", "is_verified"]
