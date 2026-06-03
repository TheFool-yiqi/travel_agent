"""Message schema tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse


def test_message_create_defaults() -> None:
    body = MessageCreate(content="你好")
    assert body.role == "user"
    assert body.content == "你好"


def test_message_response_maps_extra_info_to_metadata() -> None:
    now = datetime.now(timezone.utc)
    conv_id = uuid.uuid4()
    msg = Message(
        id=uuid.uuid4(),
        conversation_id=conv_id,
        role="assistant",
        content="回复",
        extra_info={"tool": "search"},
        created_at=now,
        updated_at=now,
    )
    resp = MessageResponse.model_validate(msg)
    assert resp.conversation_id == conv_id
    assert resp.metadata == {"tool": "search"}
    dumped = resp.model_dump()
    assert dumped["metadata"] == {"tool": "search"}
    assert "extra_info" not in dumped
