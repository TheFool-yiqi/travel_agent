"""Unit tests for ORM base and model metadata (no live database)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import inspect

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.db.models import Itinerary, Message, TravelSession, User


def test_explicit_table_names() -> None:
    assert User.__tablename__ == "users"
    assert TravelSession.__tablename__ == "travel_sessions"
    assert Message.__tablename__ == "messages"
    assert Itinerary.__tablename__ == "itineraries"


def test_base_auto_tablename_for_unspecified_models() -> None:
    class AutoNameProbe(UUIDPrimaryKeyMixin, Base):
        """Uses Base ``__tablename__`` directive (CamelCase → snake + s)."""

    assert AutoNameProbe.__tablename__ == "auto_name_probes"


def test_user_to_dict_serializes_uuid_and_datetime() -> None:
    now = datetime(2026, 6, 2, 12, 0, 0, tzinfo=timezone.utc)
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        username="traveler",
        email="traveler@example.com",
        password_hash="hashed",
        preferences={"locale": "zh-CN"},
        display_name="Traveler",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    data = user.to_dict()
    assert data["id"] == str(user_id)
    assert data["username"] == "traveler"
    assert data["email"] == "traveler@example.com"
    assert data["password_hash"] == "hashed"
    assert data["preferences"] == {"locale": "zh-CN"}
    assert data["created_at"] == now.isoformat()
    assert data["updated_at"] == now.isoformat()


def test_message_to_dict_includes_extra_info() -> None:
    now = datetime.now(timezone.utc)
    conv_id = uuid.uuid4()
    message = Message(
        id=uuid.uuid4(),
        conversation_id=conv_id,
        role="assistant",
        content="Hello",
        extra_info={"tool": "search"},
        created_at=now,
        updated_at=now,
    )
    data = message.to_dict()
    assert data["role"] == "assistant"
    assert data["content"] == "Hello"
    assert data["extra_info"] == {"tool": "search"}
    assert data["session_id"] == str(conv_id)
    assert message.session_id == conv_id
    assert message.content_metadata == {"tool": "search"}


def test_registered_tables_in_metadata() -> None:
    tables = set(Base.metadata.tables.keys())
    assert {"users", "travel_sessions", "messages", "itineraries"}.issubset(tables)


def test_user_username_unique_constraint() -> None:
    mapper = inspect(User)
    assert mapper.columns["username"].unique is True


def test_user_email_unique_constraint() -> None:
    mapper = inspect(User)
    email_col = mapper.columns["email"]
    assert email_col.unique is True


def test_user_conversations_relationship() -> None:
    mapper = inspect(User)
    rel = mapper.relationships["conversations"]
    assert rel.back_populates == "user"
    assert rel.cascade is not None


def test_travel_session_defaults_and_extra_info() -> None:
    now = datetime.now(timezone.utc)
    session = TravelSession(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="新对话",
        status="active",
        extra_info={"current_step": "collect_requirements"},
        created_at=now,
        updated_at=now,
    )
    data = session.to_dict()
    assert data["title"] == "新对话"
    assert data["status"] == "active"
    assert data["extra_info"] == {"current_step": "collect_requirements"}


def test_message_conversation_relationship() -> None:
    mapper = inspect(Message)
    rel = mapper.relationships["conversation"]
    assert rel.back_populates == "messages"


def test_conversation_is_travel_session_alias() -> None:
    from app.db.models import Conversation

    assert Conversation is TravelSession


def test_travel_session_foreign_key_to_users() -> None:
    mapper = inspect(TravelSession)
    fk = list(mapper.columns["user_id"].foreign_keys)[0]
    assert fk.column.table.name == "users"


def test_message_foreign_key_to_travel_sessions() -> None:
    mapper = inspect(Message)
    col = mapper.columns["conversation_id"]
    assert col.name == "session_id"
    fk = list(col.foreign_keys)[0]
    assert fk.column.table.name == "travel_sessions"
