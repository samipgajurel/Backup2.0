import csv
import secrets
from io import TextIOWrapper

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError

from .models import User, EmailVerificationToken, PasswordResetToken
from .serializers import (
    SignupSerializer, VerifyEmailSerializer, UserMeSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer
)
from .permissions import IsAdmin
from .tokens import new_token


WEBMAIL_URL = "https://webmail.migadu.com/"


# -------------------- EMAIL HELPERS --------------------
def send_verification_email(user: User):
    token = new_token(16)
    EmailVerificationToken.objects.create(user=user, token=token)

    verify_url = f"{settings.FRONTEND_BASE_URL}/verify.html?token={token}"
    subject = "Verify your Codavatar InternTrack account"
    message = f"Hello {user.full_name},\n\nPlease verify your account:\n{verify_url}\n\n- Codavatar Tech"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)


def send_reset_email(user: User, token: str):
    reset_url = f"{settings.FRONTEND_BASE_URL}/reset_password.html?token={token}"
    subject = "Reset your Codavatar InternTrack password"
    message = f"Hello {user.full_name},\n\nReset your password using this link:\n{reset_url}\n\n- Codavatar Tech"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)


def send_credentials_email(user: User, password: str):
    subject = "Your Codavatar InternTrack Login Credentials"
    message = (
        f"Hello {user.full_name},\n\n"
        f"Your account has been created by Codavatar Tech.\n"
        f"Email: {user.email}\n"
        f"Password: {password}\n\n"
        f"Login: {settings.FRONTEND_BASE_URL}/login.html\n\n"
        f"- Codavatar Tech"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)


# -------------------- ME --------------------
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserMeSerializer(request.user).data)


# -------------------- SIGNUP (SELF-SIGNUP = NOT VERIFIED) --------------------
class SignupView(APIView):
    permission_classes = []

    def post(self, request):
        ser = SignupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        email = ser.validated_data["email"].lower().strip()
        full_name = ser.validated_data["full_name"].strip()
        role = ser.validated_data["role"]
        password = ser.validated_data["password"]

        if User.objects.filter(email=email).exists():
            return Response({"detail": "Email already exists"}, status=400)

        # ✅ Self signup: not verified until admin/company approves
        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            role=role,
            is_verified=False,
        )

        # You can still send a verification email for email ownership
        # but DO NOT set is_verified=True from email verify if admin approval is required.
        send_verification_email(user)

        return Response({
            "detail": "Signup successful. Please verify your email in webmail, then wait for admin/company approval.",
            "action": "VERIFY_EMAIL",
            "redirect_url": WEBMAIL_URL
        }, status=201)


# -------------------- VERIFY EMAIL (EMAIL OWNERSHIP ONLY) --------------------
class VerifyEmailView(APIView):
    permission_classes = []

    def post(self, request):
        ser = VerifyEmailSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        token = ser.validated_data["token"]

        try:
            t = EmailVerificationToken.objects.select_related("user").get(token=token, used=False)
        except EmailVerificationToken.DoesNotExist:
            return Response({"detail": "Invalid/expired token"}, status=400)

        t.used = True
        t.save(update_fields=["used"])

        # ✅ IMPORTANT:
        # We do NOT set user.is_verified=True here because you said:
        # "if admin gives data then it will automatically be verified"
        # So verification = company/admin approval, not just email link.
        return Response({
            "detail": "Email verified successfully. Please wait for admin/company approval.",
            "action": "WAIT_ADMIN_APPROVAL"
        }, status=200)


# -------------------- VERIFIED-ONLY JWT (WITH MIGADU REDIRECT INFO) --------------------
class VerifiedTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        if not user.is_verified:
            # ✅ Return structured error payload for frontend redirect
            raise ValidationError({
                "detail": "Your account is not verified yet. Please verify your email and wait for admin/company approval.",
                "action": "VERIFY_EMAIL",
                "redirect_url": WEBMAIL_URL
            })

        return data


class VerifiedTokenObtainPairView(TokenObtainPairView):
    serializer_class = VerifiedTokenSerializer


# -------------------- FORGOT / RESET PASSWORD --------------------
class ForgotPasswordView(APIView):
    permission_classes = []

    def post(self, request):
        ser = ForgotPasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email = ser.validated_data["email"].lower().strip()

        user = User.objects.filter(email=email).first()
        # Always return OK for security
        if not user:
            return Response({"detail": "If that email exists, a reset link was sent."})

        token = new_token(16)
        PasswordResetToken.objects.create(user=user, token=token)

        send_reset_email(user, token)
        return Response({"detail": "If that email exists, a reset link was sent."})


class ResetPasswordView(APIView):
    permission_classes = []

    def post(self, request):
        ser = ResetPasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        token = ser.validated_data["token"]
        new_password = ser.validated_data["new_password"]

        try:
            t = PasswordResetToken.objects.select_related("user").get(token=token, used=False)
        except PasswordResetToken.DoesNotExist:
            return Response({"detail": "Invalid/expired token"}, status=400)

        t.used = True
        t.save(update_fields=["used"])

        u = t.user
        u.set_password(new_password)
        u.save(update_fields=["password"])

        return Response({"detail": "Password reset successful. You can login now."})


# -------------------- ADMIN USERS --------------------
class AdminUsersView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        interns = User.objects.filter(role="INTERN").order_by("full_name")
        supervisors = User.objects.filter(role="SUPERVISOR").order_by("full_name")

        return Response({
            "interns": UserMeSerializer(interns, many=True).data,
            "supervisors": UserMeSerializer(supervisors, many=True).data,
        })


class AdminDeleteUserView(APIView):
    permission_classes = [IsAdmin]

    def delete(self, request, user_id):
        if request.user.id == user_id:
            return Response({"detail": "You cannot delete yourself"}, status=400)

        User.objects.filter(id=user_id).delete()
        return Response({"detail": "User deleted"})


# -------------------- ADMIN CSV IMPORT (AUTO-VERIFY) ✅ NEW --------------------
class AdminImportUsersCSVView(APIView):
    """
    Admin uploads company CSV -> create/update users -> auto-verified users.
    CSV columns supported (case-insensitive):
      email, full_name, role, employee_id, department, supervisor_email
    """
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

    @transaction.atomic
    def post(self, request):
        f = request.FILES.get("file")
        if not f:
            return Response({"detail": "CSV file is required. Use form-data field name: file"}, status=400)

        # Read CSV
        reader = csv.DictReader(TextIOWrapper(f.file, encoding="utf-8", newline=""))
        if not reader.fieldnames:
            return Response({"detail": "CSV has no header."}, status=400)

        # Normalize headers to lowercase
        headers = [h.strip().lower() for h in reader.fieldnames]

        required = ["email", "full_name", "role"]
        for r in required:
            if r not in headers:
                return Response({"detail": f"CSV missing required column: {r}"}, status=400)

        created = 0
        updated = 0
        errors = []
        credentials_sent = 0

        # First pass: create supervisors first
        rows = list(reader)

        def get_val(row, key):
            # handle case-insensitive keys
            for k in row.keys():
                if k and k.strip().lower() == key:
                    return (row.get(k) or "").strip()
            return ""

        # Create supervisors first
        for row in rows:
            role = get_val(row, "role").upper()
            if role != "SUPERVISOR":
                continue

            email = get_val(row, "email").lower()
            full_name = get_val(row, "full_name")
            employee_id = get_val(row, "employee_id")
            department = get_val(row, "department")

            if not email or not full_name:
                errors.append({"email": email, "error": "Missing email/full_name"})
                continue

            user, was_created = User.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": full_name,
                    "role": "SUPERVISOR",
                    "employee_id": employee_id,
                    "department": department,
                    "is_verified": True,  # ✅ company/admin data => auto-verified
                }
            )

            if was_created:
                pwd = new_token(10)
                user.set_password(pwd)
                user.save()
                created += 1
                send_credentials_email(user, pwd)
                credentials_sent += 1
            else:
                # update and ensure verified
                changed = False
                if user.full_name != full_name:
                    user.full_name = full_name
                    changed = True
                if user.role != "SUPERVISOR":
                    user.role = "SUPERVISOR"
                    changed = True
                if employee_id and user.employee_id != employee_id:
                    user.employee_id = employee_id
                    changed = True
                if department and user.department != department:
                    user.department = department
                    changed = True
                if not user.is_verified:
                    user.is_verified = True
                    changed = True
                if changed:
                    user.save()
                    updated += 1

        # Second pass: create interns and attach supervisor
        for row in rows:
            role = get_val(row, "role").upper()
            if role != "INTERN":
                continue

            email = get_val(row, "email").lower()
            full_name = get_val(row, "full_name")
            employee_id = get_val(row, "employee_id")
            department = get_val(row, "department")
            supervisor_email = get_val(row, "supervisor_email").lower()

            if not email or not full_name:
                errors.append({"email": email, "error": "Missing email/full_name"})
                continue

            supervisor = None
            if supervisor_email:
                supervisor = User.objects.filter(email=supervisor_email, role="SUPERVISOR").first()

            user, was_created = User.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": full_name,
                    "role": "INTERN",
                    "employee_id": employee_id,
                    "department": department,
                    "supervisor": supervisor,
                    "is_verified": True,  # ✅ company/admin data => auto-verified
                }
            )

            if was_created:
                pwd = new_token(10)
                user.set_password(pwd)
                user.save()
                created += 1
                send_credentials_email(user, pwd)
                credentials_sent += 1
            else:
                changed = False
                if user.full_name != full_name:
                    user.full_name = full_name
                    changed = True
                if user.role != "INTERN":
                    user.role = "INTERN"
                    changed = True
                if employee_id and user.employee_id != employee_id:
                    user.employee_id = employee_id
                    changed = True
                if department and user.department != department:
                    user.department = department
                    changed = True
                if supervisor and user.supervisor_id != supervisor.id:
                    user.supervisor = supervisor
                    changed = True
                if not user.is_verified:
                    user.is_verified = True
                    changed = True
                if changed:
                    user.save()
                    updated += 1

        return Response({
            "detail": "CSV import completed.",
            "created": created,
            "updated": updated,
            "credentials_sent": credentials_sent,
            "errors_count": len(errors),
            "errors": errors[:50],
        }, status=200)
