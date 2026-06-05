from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from argon2 import PasswordHasher, exceptions

from app.models.user import User

_PASSWORD_HASHER = PasswordHasher()
_JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "dev-secret"
_JWT_EXPIRATION_SECONDS = int(os.getenv("JWT_EXPIRATION_SECONDS", "3600"))

SUPPORTED_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _PASSWORD_HASHER.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _PASSWORD_HASHER.verify(password_hash, password)
    except exceptions.VerifyMismatchError:
        return False
    except exceptions.VerificationError:
        return False


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("utf-8")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign_token(message: bytes) -> str:
    signature = hmac.new(_JWT_SECRET.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url_encode(signature)


def create_access_token(user: User, expires_in: int | None = None) -> str:
    expiration = int(time.time()) + (expires_in or _JWT_EXPIRATION_SECONDS)
    header = {"alg": SUPPORTED_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": expiration,
    }
    encoded_header = _b64url_encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    encoded_payload = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    message = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = _sign_token(message)
    return f"{encoded_header}.{encoded_payload}.{signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise ValueError("Invalid authentication token") from exc

    header_bytes = _b64url_decode(header_segment)
    payload_bytes = _b64url_decode(payload_segment)
    signature = _b64url_decode(signature_segment)

    header = json.loads(header_bytes)
    payload = json.loads(payload_bytes)

    if header.get("alg") != SUPPORTED_ALGORITHM:
        raise ValueError("Invalid token algorithm")

    message = f"{header_segment}.{payload_segment}".encode("utf-8")
    expected_signature = hmac.new(_JWT_SECRET.encode("utf-8"), message, hashlib.sha256).digest()
    if not hmac.compare_digest(expected_signature, signature):
        raise ValueError("Invalid authentication token")

    if not isinstance(payload, dict) or "exp" not in payload:
        raise ValueError("Invalid authentication token")

    if int(payload["exp"]) < int(time.time()):
        raise ValueError("Authentication token has expired")

    return payload
