"""消息 API 请求/响应模型（ORM：Message；Handoffs metadata ↔ extra_info）。"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MessageRole = Literal["user", "assistant", "system", "tool"]


class MessageCreate(BaseModel):
    """创建消息（默认 user 角色）。"""

    content: str = Field(..., min_length=1)
    role: MessageRole = "user"
    extra_info: dict[str, Any] | None = None

    @field_validator("content")
    @classmethod
    def strip_non_empty_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("消息内容不能为空")
        return stripped


class MessageResponse(BaseModel):
    """消息响应"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="extra_info")
    created_at: datetime
