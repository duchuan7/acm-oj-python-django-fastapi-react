import secrets

import redis
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import serializers


def _client():
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def _rate_limit(client, key, limit, seconds, message):
    count = client.incr(key)
    if count == 1:
        client.expire(key, seconds)
    if count > limit:
        raise serializers.ValidationError(message)


def send_registration_code(email, ip_address):
    client = _client()
    normalized_email = email.strip().lower()
    _rate_limit(
        client,
        f"register-code:cooldown:{normalized_email}",
        1,
        settings.REGISTRATION_CODE_COOLDOWN_SECONDS,
        "Please wait before requesting another verification code.",
    )
    _rate_limit(
        client,
        f"register-code:ip:{ip_address}",
        settings.REGISTRATION_CODE_IP_LIMIT,
        settings.REGISTRATION_CODE_IP_WINDOW_SECONDS,
        "Too many verification code requests from this address. Please try again later.",
    )
    code = f"{secrets.randbelow(1_000_000):06d}"
    client.setex(
        f"register-code:value:{normalized_email}",
        settings.REGISTRATION_CODE_TTL_SECONDS,
        code,
    )
    send_mail(
        subject="duilio OJ registration verification code",
        message=f"Your duilio OJ verification code is {code}. It expires in 10 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[normalized_email],
        fail_silently=False,
    )


def consume_registration_code(email, code):
    client = _client()
    normalized_email = email.strip().lower()
    attempt_key = f"register-code:attempt:{normalized_email}"
    _rate_limit(
        client,
        attempt_key,
        settings.REGISTRATION_CODE_VERIFY_LIMIT,
        settings.REGISTRATION_CODE_TTL_SECONDS,
        "Too many verification attempts. Please request a new code later.",
    )
    key = f"register-code:value:{normalized_email}"
    expected = client.get(key)
    if not expected or not secrets.compare_digest(expected, str(code).strip()):
        raise serializers.ValidationError("Invalid or expired email verification code.")
    client.delete(key, attempt_key)
