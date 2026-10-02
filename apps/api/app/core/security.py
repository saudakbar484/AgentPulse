import base64
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet
from app.core.config import get_settings

ph = PasswordHasher()
settings = get_settings()


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, password)
    except VerifyMismatchError:
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def generate_api_key(prefix: str = "ag_live_") -> tuple[str, str, str]:
    """Generates (raw_key, key_prefix, key_hash).

    The raw_key is shown only once to the user.
    """
    random_part = secrets.token_urlsafe(32)
    raw_key = f"{prefix}{random_part}"
    key_prefix = raw_key[:12]
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return raw_key, key_prefix, key_hash


def verify_api_key(raw_key: str, key_hash: str) -> bool:
    computed = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return secrets.compare_digest(computed, key_hash)


def _get_fernet() -> Fernet:
    try:
        key = settings.CREDENTIAL_ENCRYPTION_KEY.encode("utf-8")
        return Fernet(key)
    except Exception:
        # Fallback for development if key invalid
        fallback = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
        return Fernet(fallback)


def encrypt_secret(secret_text: str) -> str:
    f = _get_fernet()
    return f.encrypt(secret_text.encode("utf-8")).decode("utf-8")


def decrypt_secret(encrypted_text: str) -> str:
    f = _get_fernet()
    return f.decrypt(encrypted_text.encode("utf-8")).decode("utf-8")
