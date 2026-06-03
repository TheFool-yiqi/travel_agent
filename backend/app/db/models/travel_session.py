"""规划会话模型（Handoffs Conversation 对齐，表名 travel_sessions）。"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# 会话状态：active / archived / deleted
SESSION_STATUS_ACTIVE = "active"
SESSION_STATUS_ARCHIVED = "archived"
SESSION_STATUS_DELETED = "deleted"


class TravelSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """业务会话表；LangGraph thread_id 可选绑定。"""

    __tablename__ = "travel_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        default="新对话",
        nullable=False,
        server_default="新对话",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=SESSION_STATUS_ACTIVE,
        nullable=False,
        server_default=SESSION_STATUS_ACTIVE,
        index=True,
    )
    extra_info: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    # Route 1：LangGraph configurable.thread_id
    thread_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True, unique=True, index=True
    )

    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


# Handoffs 兼容别名
Conversation = TravelSession
