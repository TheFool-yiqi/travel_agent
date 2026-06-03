"""Security helpers unit tests."""

from __future__ import annotations

from datetime import timedelta

import jwt
import pytest

from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.settings import settings


def test_hash_and_verify_password_roundtrip() -> None:
    hashed = hash_password("TravelAgent123!")
    assert hashed != "TravelAgent123!"
    assert verify_password("TravelAgent123!", hashed)
    assert not verify_password("wrong", hashed)


def test_verify_password_rejects_invalid_hash() -> None:
    assert not verify_password("pwd", "not-a-bcrypt-hash")


def test_create_and_decode_access_token() -> None:
    token = create_access_token({"sub": "user-1", "username": "traveler"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-1"
    assert payload["username"] == "traveler"
    assert "exp" in payload


def test_decode_access_token_expired() -> None:
    token = create_access_token(
        {"sub": "user-1"},
        expires_delta=timedelta(seconds=-1),
    )
    assert decode_access_token(token) is None


def test_decode_access_token_invalid() -> None:
    assert decode_access_token("not.a.jwt") is None


def test_decode_access_token_wrong_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "jwt_secret_key", "test-secret-a")
    token = create_access_token({"sub": "user-1"})
    monkeypatch.setattr(settings, "jwt_secret_key", "test-secret-b")
    assert decode_access_token(token) is None


def test_jwt_uses_settings_algorithm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "jwt_secret_key", "algo-test-secret")
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    token = create_access_token({"sub": "x"})
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
