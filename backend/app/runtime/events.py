"""PlanningRuntime internal event contract."""

from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.runtime.manifest import is_valid_stage

RuntimeEventType = Literal[
    "stage_started",
    "stage_completed",
    "token_delta",
    "approval_required",
    "runtime_completed",
    "runtime_failed",
]
RuntimeEventVisibility = Literal["public", "internal", "external_trace"]


class RuntimeEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    stage: str | None
    type: RuntimeEventType
    visibility: RuntimeEventVisibility
    payload: dict[str, Any] = Field(default_factory=dict)


def make_stage_started_event(*, run_id: str, stage: str) -> RuntimeEvent:
    """Create a public stage-started event."""
    _require_valid_stage(stage)
    return RuntimeEvent(
        run_id=run_id,
        stage=stage,
        type="stage_started",
        visibility="public",
    )


def make_stage_completed_event(
    *,
    run_id: str,
    stage: str,
    output: dict[str, Any] | None = None,
) -> RuntimeEvent:
    """Create a public stage-completed event."""
    _require_valid_stage(stage)
    payload = {"output": dict(output)} if output is not None else {}
    return RuntimeEvent(
        run_id=run_id,
        stage=stage,
        type="stage_completed",
        visibility="public",
        payload=payload,
    )


def make_runtime_completed_event(*, run_id: str) -> RuntimeEvent:
    """Create the public terminal event for a completed runtime run."""
    return RuntimeEvent(
        run_id=run_id,
        stage=None,
        type="runtime_completed",
        visibility="public",
    )


def make_runtime_failed_event(
    *,
    run_id: str,
    error: dict[str, Any],
    stage: str | None = None,
    visibility: RuntimeEventVisibility = "public",
) -> RuntimeEvent:
    """Create a terminal failure event with structured error details."""
    if stage is not None:
        _require_valid_stage(stage)
    return RuntimeEvent(
        run_id=run_id,
        stage=stage,
        type="runtime_failed",
        visibility=visibility,
        payload={"error": dict(error)},
    )


def runtime_event_to_transport(event: RuntimeEvent) -> dict[str, Any]:
    """Convert an internal RuntimeEvent to the stable runtime transport shape."""
    return {
        "type": "runtime_event",
        "event_type": event.type,
        "stage": event.stage,
        "visibility": event.visibility,
        "payload": dict(event.payload),
    }


def _require_valid_stage(stage: str) -> None:
    if not is_valid_stage(stage):
        raise ValueError(f"Unknown runtime stage: {stage}")
