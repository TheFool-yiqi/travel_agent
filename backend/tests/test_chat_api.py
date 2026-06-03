"""Chat SSE API tests."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user
from app.db.models.travel_session import TravelSession
from app.db.models.user import User
from app.db.session import get_db
from app.main import app


@pytest.fixture
def active_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid.uuid4(),
        username="alice",
        email="alice@example.com",
        password_hash="x",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
async def authed_client(active_user: User):
    async def _override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: active_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, active_user
    app.dependency_overrides.clear()


async def _fake_sse_stream(*_args, **_kwargs) -> AsyncIterator[str]:
    yield 'data: {"type":"token","content":"你好"}\n\n'
    yield 'data: {"type":"done"}\n\n'


@pytest.mark.asyncio
async def test_stream_chat_sse(authed_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, _user = authed_client
    monkeypatch.setattr(
        "app.api.v1.chat.generate_sse_stream",
        _fake_sse_stream,
    )
    cid = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/chat/stream/{cid}",
        json={"content": "想去成都"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert "token" in resp.text
    assert "done" in resp.text


@pytest.mark.asyncio
async def test_chat_history_not_found(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authed_client
    monkeypatch.setattr(
        "app.api.v1.chat.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=None),
    )
    resp = await client.get(f"/api/v1/chat/history/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_chat_history_success(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authed_client
    now = datetime.now(timezone.utc)
    travel_session = TravelSession(
        id=uuid.uuid4(),
        user_id=user.id,
        title="测试",
        status="active",
        extra_info={},
        created_at=now,
        updated_at=now,
    )
    monkeypatch.setattr(
        "app.api.v1.chat.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=travel_session),
    )
    monkeypatch.setattr(
        "app.api.v1.chat.MessageRepository.list_for_conversation",
        AsyncMock(return_value=[]),
    )
    resp = await client.get(f"/api/v1/chat/history/{travel_session.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["conversation"]["title"] == "测试"
    assert body["messages"] == []


@pytest.mark.asyncio
async def test_chat_history_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/chat/history/{uuid.uuid4()}")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_stream_chat_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/chat/stream/{uuid.uuid4()}",
            json={"content": "hello"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_chat_history_invalid_uuid(authed_client) -> None:
    client, _user = authed_client
    resp = await client.get("/api/v1/chat/history/not-a-uuid")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "无效的会话 ID"


@pytest.mark.asyncio
async def test_stream_chat_invalid_uuid(authed_client) -> None:
    client, _user = authed_client
    resp = await client.post(
        "/api/v1/chat/stream/not-a-uuid",
        json={"content": "hello"},
    )
    assert resp.status_code == 400
