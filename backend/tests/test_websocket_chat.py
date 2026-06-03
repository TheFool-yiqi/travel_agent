"""WebSocket chat stream tests (TC-CHAT-010~013, TC-SEC-012)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.db.models.user import User
from app.main import app
from app.security.jwt import create_access_token


def _active_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid.uuid4(),
        username="ws_user",
        email="ws@example.com",
        password_hash="x",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _mock_session_factory(user: User) -> MagicMock:
    db = AsyncMock()
    factory = MagicMock()
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=db)
    ctx.__aexit__ = AsyncMock(return_value=None)
    factory.return_value = ctx
    return factory


async def _fake_chat_events(*_args, **_kwargs) -> AsyncIterator[dict]:
    yield {"type": "token", "content": "你好"}
    yield {"type": "done"}


@pytest.fixture
def ws_user(monkeypatch: pytest.MonkeyPatch) -> User:
    user = _active_user()
    factory = _mock_session_factory(user)
    monkeypatch.setattr("app.ws.chat_stream.get_session_factory", lambda: factory)
    monkeypatch.setattr(
        "app.ws.chat_stream.UserRepository",
        lambda db: MagicMock(get_by_id=AsyncMock(return_value=user)),
    )
    return user


def test_ws_query_token_auth(ws_user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CHAT-010: WebSocket query ?token= authentication."""
    monkeypatch.setattr("app.ws.chat_stream.iter_chat_events", _fake_chat_events)
    token = create_access_token({"sub": str(ws_user.id)})
    cid = uuid.uuid4()

    client = TestClient(app)
    with client.websocket_connect(f"/api/v1/chat/ws/{cid}?token={token}") as ws:
        ws.send_json({"type": "message", "content": "你好"})
        first = ws.receive_json()
        assert first["type"] == "token"
        second = ws.receive_json()
        assert second["type"] == "done"


def test_ws_auth_frame(ws_user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CHAT-011: first-frame auth {"type":"auth","token":"..."}."""
    monkeypatch.setattr("app.ws.chat_stream.iter_chat_events", _fake_chat_events)
    token = create_access_token({"sub": str(ws_user.id)})
    cid = uuid.uuid4()

    client = TestClient(app)
    with client.websocket_connect(f"/api/v1/chat/ws/{cid}") as ws:
        ws.send_json({"type": "auth", "token": token})
        ws.send_json({"type": "message", "content": "你好"})
        first = ws.receive_json()
        assert first["type"] == "token"


@pytest.mark.asyncio
async def test_ws_invalid_token_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CHAT-012 / TC-SEC-012: invalid token → authenticate returns None."""
    from app.ws.chat_stream import authenticate_websocket

    user = _active_user()
    factory = _mock_session_factory(user)
    monkeypatch.setattr("app.ws.chat_stream.get_session_factory", lambda: factory)
    monkeypatch.setattr(
        "app.ws.chat_stream.UserRepository",
        lambda db: MagicMock(get_by_id=AsyncMock(return_value=None)),
    )

    websocket = MagicMock()
    websocket.query_params = MagicMock()
    websocket.query_params.get = lambda key, default=None: (
        "bad.token.value" if key == "token" else default
    )
    websocket.accept = AsyncMock()
    websocket.close = AsyncMock()

    result = await authenticate_websocket(websocket)
    assert result is None
    websocket.close.assert_awaited()
    assert websocket.close.await_args.kwargs.get("code") == 4401


def test_ws_message_events(ws_user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CHAT-013: message frame yields token + done events."""
    monkeypatch.setattr("app.ws.chat_stream.iter_chat_events", _fake_chat_events)
    token = create_access_token({"sub": str(ws_user.id)})
    cid = uuid.uuid4()

    client = TestClient(app)
    with client.websocket_connect(f"/api/v1/chat/ws/{cid}?token={token}") as ws:
        ws.send_json({"type": "ping"})
        assert ws.receive_json() == {"type": "pong"}

        ws.send_json({"type": "message", "content": "测试"})
        events = [ws.receive_json(), ws.receive_json()]
        types = {e["type"] for e in events}
        assert types == {"token", "done"}


def test_ws_empty_content_error(ws_user: User) -> None:
    """TC-CHAT-008: empty message content returns error frame."""
    token = create_access_token({"sub": str(ws_user.id)})
    cid = uuid.uuid4()

    client = TestClient(app)
    with client.websocket_connect(f"/api/v1/chat/ws/{cid}?token={token}") as ws:
        ws.send_json({"type": "message", "content": "   "})
        payload = ws.receive_json()
        assert payload["type"] == "error"
        assert "不能为空" in payload["message"]
