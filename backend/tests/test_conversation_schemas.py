"""Conversation schema tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.db.models.travel_session import TravelSession
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    TravelSessionResponse,
)


def test_conversation_create_defaults() -> None:
    body = ConversationCreate()
    assert body.title == "新对话"
    assert body.thread_id is None


def test_conversation_update_validates_status() -> None:
    with pytest.raises(ValidationError):
        ConversationUpdate(status="invalid")  # type: ignore[arg-type]


def test_conversation_response_from_orm() -> None:
    now = datetime.now(timezone.utc)
    session = TravelSession(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="成都之旅",
        status="active",
        extra_info={"step": "plan_destination"},
        thread_id="thread-abc",
        created_at=now,
        updated_at=now,
    )
    resp = ConversationResponse.model_validate(session)
    assert resp.title == "成都之旅"
    assert resp.extra_info == {"step": "plan_destination"}
    assert resp.thread_id == "thread-abc"


def test_travel_session_response_alias() -> None:
    assert TravelSessionResponse is ConversationResponse
