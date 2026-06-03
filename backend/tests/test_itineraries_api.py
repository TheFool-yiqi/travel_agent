"""Itineraries API tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user
from app.db.models.itinerary import Itinerary
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


def _itinerary(user_id: uuid.UUID, session_id: uuid.UUID, **kwargs) -> Itinerary:
    now = datetime.now(timezone.utc)
    data = {
        "id": uuid.uuid4(),
        "session_id": session_id,
        "user_id": user_id,
        "days": [{"day_number": 1, "theme": "抵达", "activities": ["宽窄巷子"]}],
        "budget": {"total": 3000},
        "summary": "成都三日游",
        "status": "draft",
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }
    data.update(kwargs)
    return Itinerary(**data)


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
async def test_get_latest_itinerary_for_session(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authed_client
    session_id = uuid.uuid4()
    itinerary = _itinerary(user.id, session_id)

    monkeypatch.setattr(
        "app.api.v1.itineraries.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=_session(user.id, id=session_id)),
    )
    monkeypatch.setattr(
        "app.api.v1.itineraries.ItineraryRepository.get_latest_for_session",
        AsyncMock(return_value=itinerary),
    )

    resp = await client.get(f"/api/v1/itineraries/sessions/{session_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == str(session_id)
    assert body["days"][0]["theme"] == "抵达"


@pytest.mark.asyncio
async def test_get_itinerary_by_id(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authed_client
    session_id = uuid.uuid4()
    itinerary = _itinerary(user.id, session_id)

    monkeypatch.setattr(
        "app.api.v1.itineraries.ItineraryRepository.get_by_id",
        AsyncMock(return_value=itinerary),
    )

    resp = await client.get(f"/api/v1/itineraries/{itinerary.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(itinerary.id)


@pytest.mark.asyncio
async def test_patch_itinerary(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authed_client
    session_id = uuid.uuid4()
    itinerary = _itinerary(user.id, session_id)
    updated = _itinerary(
        user.id,
        session_id,
        id=itinerary.id,
        days=[{"day_number": 1, "theme": "更新", "activities": ["锦里"]}],
        version=1,
    )

    get_mock = AsyncMock(return_value=itinerary)
    update_fields_mock = AsyncMock(return_value=updated)
    session_get_mock = AsyncMock(return_value=_session(user.id, id=session_id))
    session_update_mock = AsyncMock(return_value=object())

    monkeypatch.setattr(
        "app.api.v1.itineraries.ItineraryRepository.get_by_id",
        get_mock,
    )
    monkeypatch.setattr(
        "app.api.v1.itineraries.ItineraryRepository.update_fields",
        update_fields_mock,
    )
    monkeypatch.setattr(
        "app.api.v1.itineraries.TravelSessionRepository.get_for_user",
        session_get_mock,
    )
    monkeypatch.setattr(
        "app.api.v1.itineraries.TravelSessionRepository.update",
        session_update_mock,
    )

    resp = await client.patch(
        f"/api/v1/itineraries/{itinerary.id}",
        json={"summary": "更新摘要"},
    )
    assert resp.status_code == 200
    update_fields_mock.assert_awaited_once()
