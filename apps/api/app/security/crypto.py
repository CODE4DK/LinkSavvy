"""Symmetric encryption for data at rest: OAuth provider tokens and raw
profile paste/upload content (see app/profiles/service.py)."""

from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet

from app.settings import settings


@lru_cache
def _fernet() -> Fernet:
    return Fernet(settings.encryption_key.encode("utf-8"))


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")


def encrypt_bytes(plaintext: bytes) -> bytes:
    return _fernet().encrypt(plaintext)


def decrypt_bytes(ciphertext: bytes) -> bytes:
    return _fernet().decrypt(ciphertext)
