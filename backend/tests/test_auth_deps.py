"""API auth dependency tests."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import get_current_user
from app.db.models.user import User
from app.security.jwt import create_access_token


@pytest.fixture
def active_user() -> User:
    uid = uuid.uuid4()
    return User(
        id=uid,
        username="traveler",
        email="t@example.com",
        password_hash="hashed",
        is_active=True,
    )


@pytest.mark.asyncio
async def test_get_current_user_success(
    monkeypatch: pytest.MonkeyPatch, active_user: User
) -> None:
    token = create_access_token({"sub": str(active_user.id)})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    db = AsyncMock()

    async def _get_by_id(user_id: uuid.UUID) -> User | None:
        return active_user if user_id == active_user.id else None

    monkeypatch.setattr(
        "app.api.deps.UserRepository.get_by_id",
        AsyncMock(side_effect=_get_by_id),
    )

    user = await get_current_user(credentials, db)
    assert user.id == active_user.id


@pytest.mark.asyncio
async def test_get_current_user_invalid_token() -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad.token")
    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials, AsyncMock())
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_missing_sub() -> None:
    token = create_access_token({"username": "no-sub"})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials, AsyncMock())
    assert exc.value.status_code == 401
    assert "格式错误" in exc.value.detail


@pytest.mark.asyncio
async def test_get_current_user_not_found(
    monkeypatch: pytest.MonkeyPatch, active_user: User
) -> None:
    token = create_access_token({"sub": str(active_user.id)})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    monkeypatch.setattr(
        "app.api.deps.UserRepository.get_by_id",
        AsyncMock(return_value=None),
    )
    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials, AsyncMock())
    assert exc.value.status_code == 401
    assert exc.value.detail == "用户不存在"


@pytest.mark.asyncio
async def test_get_current_user_inactive(
    monkeypatch: pytest.MonkeyPatch, active_user: User
) -> None:
    active_user.is_active = False
    token = create_access_token({"sub": str(active_user.id)})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    monkeypatch.setattr(
        "app.api.deps.UserRepository.get_by_id",
        AsyncMock(return_value=active_user),
    )
    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials, AsyncMock())
    assert exc.value.status_code == 403
