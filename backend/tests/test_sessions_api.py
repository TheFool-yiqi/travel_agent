"""Sessions / conversations API tests."""

from __future__ import annotations

import uuid
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


def _session(user_id: uuid.UUID, **kwargs) -> TravelSession:
    now = datetime.now(timezone.utc)
    data = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "title": "新对话",
        "status": "active",
        "extra_info": {},
        "created_at": now,
        "updated_at": now,
    }
    data.update(kwargs)
    return TravelSession(**data)


@pytest.mark.asyncio
async def test_create_conversation(authed_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, user = authed_client
    created = _session(user.id, title="成都行")
    seed_mock = AsyncMock()

    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.create",
        AsyncMock(return_value=created),
    )
    monkeypatch.setattr(
        "app.api.v1.sessions.seed_initial_greeting",
        seed_mock,
    )

    resp = await client.post("/api/v1/sessions", json={"title": "成都行"})
    assert resp.status_code == 201
    assert resp.json()["title"] == "成都行"
    seed_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_conversations(authed_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, user = authed_client
    sessions = [_session(user.id), _session(user.id, title="B")]

    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.list_for_user",
        AsyncMock(return_value=sessions),
    )

    resp = await client.get("/api/v1/conversations")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_conversation_not_found(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _user = authed_client
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=None),
    )
    resp = await client.get(f"/api/v1/sessions/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_conversation_soft(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authed_client
    session = _session(user.id)
    update_mock = AsyncMock(return_value=session)

    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=session),
    )
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.update",
        update_mock,
    )

    resp = await client.delete(f"/api/v1/sessions/{session.id}")
    assert resp.status_code == 200
    assert resp.json()["message"] == "会话已删除"
    update_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_conversation_success(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authed_client
    session = _session(user.id, title="成都三日游")
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=session),
    )
    resp = await client.get(f"/api/v1/sessions/{session.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(session.id)
    assert body["title"] == "成都三日游"


@pytest.mark.asyncio
async def test_get_deleted_conversation_404(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authed_client
    session = _session(user.id, status="deleted")
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=session),
    )
    resp = await client.get(f"/api/v1/sessions/{session.id}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "会话不存在"


@pytest.mark.asyncio
async def test_create_conversation_default_title(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authed_client
    created = _session(user.id, title="新对话")
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.create",
        AsyncMock(return_value=created),
    )
    monkeypatch.setattr(
        "app.api.v1.sessions.seed_initial_greeting",
        AsyncMock(),
    )
    resp = await client.post("/api/v1/sessions", json={})
    assert resp.status_code == 201
    assert resp.json()["title"] == "新对话"


@pytest.mark.asyncio
async def test_list_excludes_deleted(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authed_client
    active = _session(user.id, title="Active")
    list_mock = AsyncMock(return_value=[active])
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.list_for_user",
        list_mock,
    )
    resp = await client.get("/api/v1/sessions")
    assert resp.status_code == 200
    titles = [s["title"] for s in resp.json()]
    assert titles == ["Active"]
    list_mock.assert_awaited_once()
    assert list_mock.await_args.kwargs.get("exclude_deleted") is True


@pytest.mark.asyncio
async def test_create_session_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/sessions", json={"title": "x"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_uuid_session_id(authed_client) -> None:
    client, _user = authed_client
    resp = await client.get("/api/v1/sessions/not-a-uuid")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "无效的会话 ID"


@pytest.mark.asyncio
async def test_update_session_title(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authed_client
    session = _session(user.id)
    updated = _session(user.id, title="成都三日游")
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=session),
    )
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.update",
        AsyncMock(return_value=updated),
    )
    resp = await client.patch(
        f"/api/v1/sessions/{session.id}",
        json={"title": "成都三日游"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "成都三日游"


@pytest.mark.asyncio
async def test_create_with_extra_info(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authed_client
    extra = {"source": "test", "tags": ["demo"]}
    created = _session(user.id, extra_info=extra)
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.create",
        AsyncMock(return_value=created),
    )
    monkeypatch.setattr(
        "app.api.v1.sessions.seed_initial_greeting",
        AsyncMock(),
    )
    resp = await client.post("/api/v1/sessions", json={"extra_info": extra})
    assert resp.status_code == 201
    assert resp.json()["extra_info"] == extra


@pytest.mark.asyncio
async def test_conversations_alias_crud(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authed_client
    created = _session(user.id, title="Alias Test")
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.create",
        AsyncMock(return_value=created),
    )
    monkeypatch.setattr(
        "app.api.v1.sessions.seed_initial_greeting",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.list_for_user",
        AsyncMock(return_value=[created]),
    )
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=created),
    )

    create_resp = await client.post("/api/v1/conversations", json={"title": "Alias Test"})
    assert create_resp.status_code == 201

    list_resp = await client.get("/api/v1/conversations")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    get_resp = await client.get(f"/api/v1/conversations/{created.id}")
    assert get_resp.status_code == 200


@pytest.mark.asyncio
async def test_cross_user_session_access(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _user = authed_client
    other_session_id = uuid.uuid4()
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=None),
    )
    resp = await client.get(f"/api/v1/sessions/{other_session_id}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "会话不存在"


@pytest.mark.asyncio
async def test_create_conversation_seeds_greeting(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authed_client
    created = _session(user.id)
    create_msg = AsyncMock()

    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.create",
        AsyncMock(return_value=created),
    )
    monkeypatch.setattr(
        "app.services.conversation_bootstrap.MessageRepository.create",
        create_msg,
    )

    resp = await client.post("/api/v1/sessions", json={})
    assert resp.status_code == 201
    create_msg.assert_awaited_once()
    call_kwargs = create_msg.await_args.kwargs
    assert call_kwargs["role"] == "assistant"
    assert call_kwargs["extra_info"]["kind"] == "greeting"
