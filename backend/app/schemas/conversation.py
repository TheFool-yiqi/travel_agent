"""会话 API 请求/响应模型（ORM：TravelSession / Handoffs Conversation）。"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models.travel_session import (
    SESSION_STATUS_ACTIVE,
    SESSION_STATUS_ARCHIVED,
    SESSION_STATUS_DELETED,
)

SessionStatus = Literal["active", "archived", "deleted"]
VALID_SESSION_STATUSES = {
    SESSION_STATUS_ACTIVE,
    SESSION_STATUS_ARCHIVED,
    SESSION_STATUS_DELETED,
}


class ConversationCreate(BaseModel):
    """创建会话"""

    title: str | None = Field(default="新对话", max_length=200)
    thread_id: str | None = Field(
        default=None,
        max_length=128,
        description="LangGraph configurable.thread_id（可选）",
    )
    extra_info: dict[str, Any] | None = None


class ConversationUpdate(BaseModel):
    """更新会话"""

    title: str | None = Field(default=None, max_length=200)
    status: SessionStatus | None = None
    extra_info: dict[str, Any] | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_SESSION_STATUSES:
            raise ValueError(f"status 必须是 {sorted(VALID_SESSION_STATUSES)} 之一")
        return value


class ConversationResponse(BaseModel):
    """会话响应"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    status: str
    extra_info: dict[str, Any] = Field(default_factory=dict)
    thread_id: str | None = None
    created_at: datetime
    updated_at: datetime


# Route 1 / architecture.md 命名别名
TravelSessionResponse = ConversationResponse
