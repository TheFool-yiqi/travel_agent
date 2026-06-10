"""Finalization schemas for approval and order completion."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ApprovalStatus = Literal["pending", "approved", "revising"]
AllowedApprovalAction = Literal["approve", "reject", "modify_with_feedback"]


class PendingApproval(BaseModel):
    status: ApprovalStatus = "pending"
    itinerary_summary: str = ""
    destination: str | None = None
    travel_days: int | None = None
    assumption_summary: list[str] = Field(default_factory=list)
    evidence_card_ids: list[str] = Field(default_factory=list)
    quality_summary: dict[str, Any] = Field(default_factory=dict)
    allowed_actions: list[AllowedApprovalAction] = Field(
        default_factory=lambda: ["approve", "reject", "modify_with_feedback"],
    )
    public_prompt: str = ""

    def to_runtime_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> PendingApproval:
        return cls.model_validate(data)


class FinalizationResult(BaseModel):
    order_id: str
    final_message: str
    destination: str
    travel_days: int
    persisted: bool = False
    itinerary_id: str | None = None

    def to_runtime_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> FinalizationResult:
        return cls.model_validate(data)
