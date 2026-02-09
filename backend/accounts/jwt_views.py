from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

WEBMAIL_URL = "https://webmail.migadu.com/"

class VerifiedTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        if not getattr(self.user, "is_verified", False):
            raise serializers.ValidationError({
                "detail": "Your account is not verified yet. Please verify your email and wait for admin approval.",
                "action": "VERIFY_EMAIL",
                "redirect_url": WEBMAIL_URL
            })

        return data

class VerifiedTokenObtainPairView(TokenObtainPairView):
    serializer_class = VerifiedTokenObtainPairSerializer
