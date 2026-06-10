"""Domain planning schemas for PlanningRuntime."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PlanProposal(BaseModel):
    agent_name: str
    stage: str = "domain_plan"
    summary: str
    recommendations: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    evidence_card_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    detail: dict[str, Any] = Field(default_factory=dict)

    def to_runtime_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> PlanProposal:
        return cls.model_validate(data)


class ItineraryDraft(BaseModel):
    destination: str
    travel_days: int
    days: list[dict[str, Any]] = Field(default_factory=list)
    budget: dict[str, Any] | None = None
    summary: str = ""
    assumptions: list[str] = Field(default_factory=list)
    evidence_card_ids: list[str] = Field(default_factory=list)
    integration_notes: list[str] = Field(default_factory=list)

    def to_runtime_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> ItineraryDraft:
        return cls.model_validate(data)
