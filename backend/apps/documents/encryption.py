"""
Field-level encryption for sensitive documents at rest.
Uses Fernet (AES-128-CBC + HMAC-SHA256) — secure, audited, and standard.
"""
import logging
from base64 import urlsafe_b64encode
from hashlib import sha256
from cryptography.fernet import Fernet
from django.conf import settings

logger = logging.getLogger(__name__)


def _derive_key() -> bytes:
    """Derive Fernet key from Django SECRET_KEY (32-byte URL-safe base64)."""
    raw = settings.SECRET_KEY.encode()
    digest = sha256(raw).digest()  # 32 bytes
    return urlsafe_b64encode(digest)


_fernet = None


def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_derive_key())
    return _fernet


def encrypt_bytes(data: bytes) -> bytes:
    return get_fernet().encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    return get_fernet().decrypt(token)
