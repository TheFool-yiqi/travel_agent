"""用户账号模型（Handoffs User 对齐 + Route 1 扩展字段）。"""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Handoffs：轻量 JSON 偏好；长期记忆仍走 LangGraph Store（UserMemoryService）
    preferences: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    # Route 1 扩展（可选展示名 / 账号状态）
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Handoffs 命名 conversations；表仍为 travel_sessions
    conversations: Mapped[list["TravelSession"]] = relationship(
        "TravelSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # 别名：与 architecture.md travel_sessions 命名一致
    @property
    def travel_sessions(self) -> list["TravelSession"]:
        return self.conversations
