import secrets
from django.utils import timezone

def new_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)

def now():
    return timezone.now()
