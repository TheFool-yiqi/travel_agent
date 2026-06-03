"""semantic-metrics API 测试（P3.3）"""

from __future__ import annotations

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


@pytest.mark.asyncio
async def test_semantic_metrics_endpoint(authed_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, user = authed_client
    sid = uuid.uuid4()
    now = datetime.now(timezone.utc)
    session = TravelSession(
        id=sid,
        user_id=user.id,
        title="test",
        status="active",
        extra_info={},
        created_at=now,
        updated_at=now,
    )
    message = Message(
        id=uuid.uuid4(),
        conversation_id=sid,
        role="assistant",
        content="hi",
        extra_info={
            "semantic": {
                "metrics": {
                    "first_hit": True,
                    "slot_filled": True,
                    "clarification_asked": False,
                },
            },
        },
        created_at=now,
        updated_at=now,
    )

    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=session),
    )
    monkeypatch.setattr(
        "app.api.v1.sessions.MessageRepository.list_for_conversation",
        AsyncMock(return_value=[message]),
    )

    resp = await client.get(f"/api/v1/sessions/{sid}/semantic-metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["turns"] == 1
    assert data["first_hit_turns"] == 1
    assert data["first_hit_rate"] == 1.0


@pytest.mark.asyncio
async def test_semantic_metrics_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/sessions/{uuid.uuid4()}/semantic-metrics")
    assert resp.status_code == 401


def test_semantic_metrics_response_schema():
    from app.schemas.semantic_metrics import SemanticMetricsResponse

    payload = SemanticMetricsResponse.model_validate(
        {
            "turns": 2,
            "first_hit_turns": 1,
            "first_hit_rate": 0.5,
            "clarification_turns": 1,
            "slot_fill_turns": 1,
        },
    )
    assert payload.turns == 2
    assert payload.first_hit_rate == 0.5


@pytest.mark.asyncio
async def test_semantic_metrics_cross_user_404(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _user = authed_client
    other_id = uuid.uuid4()
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=None),
    )
    resp = await client.get(f"/api/v1/sessions/{other_id}/semantic-metrics")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "会话不存在"
