"""Users API tests (repository mocked)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.models.user import User
from app.db.session import get_db
from app.main import app
from app.security import hash_password


@pytest.fixture
def mock_db_session():
    return AsyncMock()


@pytest.fixture
async def client(mock_db_session):
    async def _override_get_db():
        try:
            yield mock_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def _sample_user(**overrides) -> User:
    now = datetime.now(timezone.utc)
    data = {
        "id": uuid.uuid4(),
        "username": "alice",
        "email": "alice@example.com",
        "password_hash": hash_password("secret12"),
        "preferences": {},
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return User(**data)


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    created = _sample_user()

    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.get_by_username",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.get_by_email",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.create",
        AsyncMock(return_value=created),
    )

    resp = await client.post(
        "/api/v1/users/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret12",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["username"] == "alice"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.get_by_username",
        AsyncMock(return_value=_sample_user()),
    )
    resp = await client.post(
        "/api/v1/users/register",
        json={
            "username": "alice",
            "email": "new@example.com",
            "password": "secret12",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "用户名已存在"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    user = _sample_user()
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.get_by_username",
        AsyncMock(return_value=user),
    )
    resp = await client.post(
        "/api/v1/users/login",
        json={"username": "alice", "password": "secret12"},
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    user = _sample_user()
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.get_by_username",
        AsyncMock(return_value=user),
    )
    resp = await client.post(
        "/api/v1/users/login",
        json={"username": "alice", "password": "wrong-password"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.get_by_username",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.get_by_email",
        AsyncMock(return_value=_sample_user()),
    )
    resp = await client.post(
        "/api/v1/users/register",
        json={
            "username": "newuser",
            "email": "alice@example.com",
            "password": "secret12",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "邮箱已被注册"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.get_by_username",
        AsyncMock(return_value=None),
    )
    resp = await client.post(
        "/api/v1/users/login",
        json={"username": "nouser", "password": "anypass"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "用户名或密码错误"


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    user = _sample_user(is_active=False)
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.get_by_username",
        AsyncMock(return_value=user),
    )
    resp = await client.post(
        "/api/v1/users/login",
        json={"username": "alice", "password": "secret12"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "账号已停用"


@pytest.mark.asyncio
async def test_me_with_valid_token(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    user = _sample_user()
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.get_by_id",
        AsyncMock(return_value=user),
    )
    from app.security import create_access_token

    token = create_access_token({"sub": str(user.id), "username": user.username})
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_responses_exclude_password_hash(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = _sample_user()
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.get_by_username",
        AsyncMock(side_effect=[None, created, created]),
    )
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.get_by_email",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.create",
        AsyncMock(return_value=created),
    )
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.get_by_id",
        AsyncMock(return_value=created),
    )

    reg = await client.post(
        "/api/v1/users/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret12",
        },
    )
    for body in (reg.json(),):
        assert "password_hash" not in body
        assert "password_hash" not in body["user"]

    login = await client.post(
        "/api/v1/users/login",
        json={"username": "alice", "password": "secret12"},
    )
    login_body = login.json()
    assert "password_hash" not in login_body
    assert "password_hash" not in login_body["user"]

    me = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {login_body['access_token']}"},
    )
    me_body = me.json()
    assert "password_hash" not in me_body


@pytest.mark.asyncio
async def test_register_weak_password_rejected(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/users/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "123",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email_rejected(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/users/register",
        json={
            "username": "alice",
            "email": "not-an-email",
            "password": "secret12",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_expired_token_rejects_me(client: AsyncClient) -> None:
    from datetime import timedelta

    from app.security import create_access_token

    token = create_access_token({"sub": "00000000-0000-0000-0000-000000000001"}, expires_delta=timedelta(seconds=-1))
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_tampered_token_rejects_me(client: AsyncClient) -> None:
    from app.security import create_access_token

    token = create_access_token({"sub": "00000000-0000-0000-0000-000000000001"})
    parts = token.split(".")
    tampered = f"{parts[0]}.{parts[1]}.invalidsignature"
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tampered}"},
    )
    assert resp.status_code == 401
