"""Secret encryption utilities for sensitive values stored in the database."""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from paper_scraper.core.config import settings


def _derive_key_from_jwt_secret(secret: str) -> bytes:
    """Derive a Fernet key when no dedicated key is configured."""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache
def get_fernet() -> Fernet:
    """Get singleton Fernet cipher instance."""
    configured = settings.MODEL_KEY_ENCRYPTION_KEY
    if configured and configured.get_secret_value():
        key = configured.get_secret_value().encode("utf-8")
    else:
        # Keep deterministic fallback for existing deployments; production should
        # provide MODEL_KEY_ENCRYPTION_KEY explicitly.
        key = _derive_key_from_jwt_secret(settings.JWT_SECRET_KEY.get_secret_value())
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    """Encrypt plaintext string for at-rest storage."""
    return get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    """Decrypt encrypted value.

    Raises:
        InvalidToken: If the value cannot be decrypted by current key.
    """
    return get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")


def try_decrypt_secret(value: str) -> str | None:
    """Best-effort decrypt helper used in migration and fallback paths."""
    try:
        return decrypt_secret(value)
    except InvalidToken:
        return None
