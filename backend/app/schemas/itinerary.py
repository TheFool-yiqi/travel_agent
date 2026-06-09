"""行程 API 请求/响应模型。"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ItineraryStatus = Literal["draft", "approved"]


class ItineraryUpdate(BaseModel):
    """手动编辑行程。"""

    days: list[dict[str, Any]] | None = None
    budget: dict[str, Any] | None = None
    summary: str | None = None
    status: ItineraryStatus | None = None


class ItineraryResponse(BaseModel):
    """行程响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    days: list[dict[str, Any]]
    budget: dict[str, Any] | None = None
    summary: str | None = None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime


class ItinerarySessionPayload(BaseModel):
    """写入 travel_sessions.extra_info.itinerary 的结构。"""

    days: list[dict[str, Any]] = Field(default_factory=list)
    budget: dict[str, Any] | None = None
    summary: str | None = None
    version: int | None = None
    itinerary_id: uuid.UUID | None = None
    status: ItineraryStatus | None = None


class OrderSessionPayload(BaseModel):
    """写入 travel_sessions.extra_info.order 的结构。"""

    order_id: str
    itinerary_id: uuid.UUID | None = None
    status: Literal["confirmed"] = "confirmed"
