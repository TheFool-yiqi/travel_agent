"""消息模型（Handoffs Message 对齐，FK 列名 session_id）。"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# 角色：user / assistant / system / tool
MESSAGE_ROLE_USER = "user"
MESSAGE_ROLE_ASSISTANT = "assistant"
MESSAGE_ROLE_SYSTEM = "system"
MESSAGE_ROLE_TOOL = "tool"


class Message(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "messages"

    # Handoffs: conversation_id；DB 列名 session_id（travel_sessions）
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        "session_id",
        UUID(as_uuid=True),
        ForeignKey("travel_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    extra_info: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=dict, nullable=True
    )

    conversation: Mapped["TravelSession"] = relationship(
        "TravelSession", back_populates="messages"
    )

    # Route 1 别名
    session_id = synonym("conversation_id")

    @property
    def session(self) -> "TravelSession":
        return self.conversation

    @property
    def content_metadata(self) -> dict[str, Any] | None:
        """向后兼容旧字段名。"""
        return self.extra_info

    @content_metadata.setter
    def content_metadata(self, value: dict[str, Any] | None) -> None:
        self.extra_info = value
