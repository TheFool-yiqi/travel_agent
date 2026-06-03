"""Automate former manual-only test cases (API / security / resilience)."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user
from app.db.models.message import Message
from app.db.models.travel_session import TravelSession
from app.db.models.user import User
from app.db.session import get_db
from app.main import app
from app.security import hash_password


@pytest.fixture
def active_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid.uuid4(),
        username="manual_auto",
        email="manual@example.com",
        password_hash=hash_password("secret12"),
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
async def client(active_user: User):
    async def _override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: active_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_cors_options_preflight(client: AsyncClient) -> None:
    """TC-API-017: CORS OPTIONS preflight returns access-control headers."""
    resp = await client.options(
        "/api/v1/users/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code in (200, 204)
    assert resp.headers.get("access-control-allow-origin")


@pytest.mark.asyncio
async def test_api_unknown_route_404(client: AsyncClient) -> None:
    """TC-API-029: unknown route returns 404."""
    resp = await client.get("/api/v1/no-such-endpoint")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_api_invalid_json_body_422(client: AsyncClient) -> None:
    """TC-API-030: malformed JSON body returns 422."""
    resp = await client.post(
        "/api/v1/users/login",
        content="{not-json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_sec_sql_injection_login_safe(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-SEC-006: SQL injection in username does not bypass auth."""
    monkeypatch.setattr(
        "app.api.v1.users.UserRepository.get_by_username",
        AsyncMock(return_value=None),
    )
    resp = await client.post(
        "/api/v1/users/login",
        json={"username": "' OR '1'='1", "password": "x"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_neg_concurrent_register_same_username(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-NEG-016: concurrent register with same username — one succeeds, one 400."""
    created_once = False

    async def _create_user(*_args, **_kwargs):
        nonlocal created_once
        if created_once:
            from fastapi import HTTPException

            raise HTTPException(status_code=400, detail="用户名已存在")
        created_once = True
        now = datetime.now(timezone.utc)
        return User(
            id=uuid.uuid4(),
            username="dup_user",
            email="a@t.com",
            password_hash="x",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

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
        _create_user,
    )

    payload = {
        "username": "dup_user",
        "email": "a@t.com",
        "password": "secret12",
    }

    results = await asyncio.gather(
        client.post("/api/v1/users/register", json=payload),
        client.post("/api/v1/users/register", json={**payload, "email": "b@t.com"}),
        return_exceptions=True,
    )
    codes = [r.status_code for r in results if hasattr(r, "status_code")]
    assert 201 in codes
    assert 400 in codes


@pytest.mark.asyncio
async def test_flow_071_old_session_single_greeting(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-FLOW-071 / TC-SESS-009: reopening session with history does not duplicate bootstrap greeting."""
    session_id = uuid.uuid4()
    session = TravelSession(
        id=session_id,
        user_id=uuid.uuid4(),
        title="旧行程",
        thread_id=str(session_id),
        status="active",
        extra_info={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    now = datetime.now(timezone.utc)
    greeting = Message(
        id=uuid.uuid4(),
        conversation_id=session_id,
        role="assistant",
        content="嗨！我是你的旅行顾问。",
        extra_info={"kind": "greeting"},
        created_at=now,
        updated_at=now,
    )

    monkeypatch.setattr(
        "app.api.v1.chat.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=session),
    )
    monkeypatch.setattr(
        "app.api.v1.chat.MessageRepository.list_for_conversation",
        AsyncMock(return_value=[greeting]),
    )

    resp = await client.get(f"/api/v1/chat/history/{session_id}")
    assert resp.status_code == 200
    body = resp.json()
    assistant_msgs = [m for m in body["messages"] if m["role"] == "assistant"]
    assert len(assistant_msgs) == 1
    assert assistant_msgs[0]["content"].startswith("嗨")


def test_neg_travel_days_extraction_ge_one() -> None:
    """TC-NEG-008: RequirementExtraction rejects travel_days < 1."""
    from pydantic import ValidationError

    from app.schemas.travel import RequirementExtraction

    with pytest.raises(ValidationError):
        RequirementExtraction(travel_days=0)
