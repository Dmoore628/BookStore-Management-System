"""Security primitives: password hashing and PII encryption.

- Passwords are hashed with bcrypt; the plaintext is never stored.
- Customer PII (name, contact) is encrypted at rest with Fernet (AES-128-CBC +
  HMAC), keyed by ENCRYPTION_KEY. Ciphertext is non-deterministic.
"""

from __future__ import annotations

import bcrypt
from cryptography.fernet import Fernet

from domain_services.config import get_settings

_BCRYPT_ROUNDS = 12


def hash_password(plaintext: str) -> str:
    """Return a salted bcrypt hash of ``plaintext``."""
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return bcrypt.hashpw(plaintext.encode("utf-8"), salt).decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """Return True iff ``plaintext`` matches the stored bcrypt ``hashed``."""
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _fernet() -> Fernet:
    return Fernet(get_settings().encryption_key.encode("utf-8"))


def encrypt(plaintext: str) -> str:
    """Encrypt ``plaintext`` for storage; returns a URL-safe token."""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    """Decrypt a token produced by :func:`encrypt`."""
    return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")

