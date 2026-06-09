"""ToolContext runtime schemas for PlanningRuntime tool enrichment."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

WeatherStatus = Literal["available", "unavailable"]


class WeatherContext(BaseModel):
    """Trimmed weather view for planners and judges; not raw MCP markdown."""

    status: WeatherStatus
    destination: str | None = None
    date_range: str | None = None
    summary: str = ""
    risks: list[str] = Field(default_factory=list)
    source: str = "qweather"
    fetched_at: str | None = None

    def to_runtime_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> WeatherContext:
        return cls.model_validate(data)


class ToolWarning(BaseModel):
    code: str
    message: str

    def to_runtime_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> ToolWarning:
        return cls.model_validate(data)


class ToolContext(BaseModel):
    weather: WeatherContext | None = None
    tool_warnings: list[ToolWarning] = Field(default_factory=list)

    def to_runtime_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> ToolContext:
        weather = data.get("weather")
        if isinstance(weather, dict):
            data = {**data, "weather": WeatherContext.from_runtime_dict(weather)}
        warnings = data.get("tool_warnings")
        if isinstance(warnings, list):
            data = {
                **data,
                "tool_warnings": [
                    ToolWarning.from_runtime_dict(item)
                    if isinstance(item, dict)
                    else item
                    for item in warnings
                ],
            }
        return cls.model_validate(data)
