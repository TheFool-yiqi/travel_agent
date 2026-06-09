"""Shared planning context schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BaseContext(BaseModel):
    planning_need_summary: dict[str, Any] = Field(default_factory=dict)
    session_facts: list[dict[str, Any]] = Field(default_factory=list)
    memory_snippets: list[dict[str, Any]] = Field(default_factory=list)
    decision_snippets: list[dict[str, Any]] = Field(default_factory=list)

    def to_runtime_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> BaseContext:
        return cls.model_validate(data)
