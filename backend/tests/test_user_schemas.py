"""User schema tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.db.models.user import User
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse


def test_user_register_validates_email_and_password() -> None:
    reg = UserRegister(username="alice", email="alice@example.com", password="secret1")
    assert reg.username == "alice"


def test_user_register_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        UserRegister(username="alice", email="alice@example.com", password="12345")


def test_user_response_from_orm() -> None:
    now = datetime.now(timezone.utc)
    orm = User(
        id=uuid.uuid4(),
        username="bob",
        email="bob@example.com",
        password_hash="hashed",
        preferences={"locale": "zh"},
        display_name="Bob",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    resp = UserResponse.model_validate(orm)
    assert resp.username == "bob"
    assert resp.preferences == {"locale": "zh"}
    assert resp.email == "bob@example.com"
    assert "password_hash" not in resp.model_dump()


def test_token_response_shape() -> None:
    now = datetime.now(timezone.utc)
    user = UserResponse(
        id=uuid.uuid4(),
        username="c",
        email="c@example.com",
        created_at=now,
    )
    token = TokenResponse(access_token="jwt.here", user=user)
    assert token.token_type == "bearer"
    assert token.user.username == "c"


def test_user_login_requires_fields() -> None:
    with pytest.raises(ValidationError):
        UserLogin(username="", password="x")
