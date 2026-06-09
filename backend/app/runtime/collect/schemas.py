"""Collect-stage structured schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

FactType = Literal["confirmed", "derived", "approved_assumption"]
FactSource = Literal["user", "rule", "discovery_confirmed", "explicit_draft_request"]


class PlanningFact(BaseModel):
    field: str
    value: Any
    fact_type: FactType
    source: FactSource


class CollectContext(BaseModel):
    trip_spec: dict[str, Any] = Field(default_factory=dict)
    conversation_state: dict[str, Any] = Field(default_factory=dict)
    discovery_state: dict[str, Any] = Field(default_factory=dict)
    readiness_state: dict[str, Any] = Field(default_factory=dict)
    pending_clarification: dict[str, Any] | None = None
    rejected_assumptions: list[dict[str, Any]] = Field(default_factory=list)


class PlanningNeed(BaseModel):
    confirmed_facts: list[PlanningFact] = Field(default_factory=list)
    derived_facts: list[PlanningFact] = Field(default_factory=list)
    approved_assumptions: list[PlanningFact] = Field(default_factory=list)
    constraints: list[dict[str, Any]] = Field(default_factory=list)
    preferences: list[dict[str, Any]] = Field(default_factory=list)
    missing_but_accepted_fields: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)

    @field_validator(
        "confirmed_facts",
        "derived_facts",
        "approved_assumptions",
        mode="before",
    )
    @classmethod
    def _validate_fact_entries(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return value
        validated: list[Any] = []
        for item in value:
            if isinstance(item, PlanningFact):
                validated.append(item)
                continue
            if not isinstance(item, dict):
                raise ValueError("PlanningNeed facts must be objects with provenance")
            if "fact_type" not in item or "source" not in item:
                raise ValueError("PlanningNeed facts require fact_type and source")
            validated.append(item)
        return validated

    def to_runtime_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> PlanningNeed:
        return cls.model_validate(data)


def collect_context_to_runtime_dict(context: CollectContext) -> dict[str, Any]:
    return context.model_dump(mode="json")


def collect_context_from_runtime_dict(data: dict[str, Any]) -> CollectContext:
    return CollectContext.model_validate(data)
