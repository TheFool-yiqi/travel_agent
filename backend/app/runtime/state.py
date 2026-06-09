"""PlanningRuntime state contract and update helpers."""

from __future__ import annotations

from typing import Any, TypedDict

from app.runtime.manifest import V1_STAGE_NAMES, is_valid_stage


class RuntimeState(TypedDict, total=False):
    run_id: str
    conversation_id: str
    user_id: str | None
    input_message: str
    current_stage: str
    completed_stages: list[str]
    stage_outputs: dict[str, dict[str, Any]]
    pending_approval: dict[str, Any] | None
    public_messages: list[dict[str, Any]]
    private_notes: list[dict[str, Any]]
    errors: list[dict[str, Any]]


def create_initial_runtime_state(
    *,
    run_id: str,
    conversation_id: str,
    input_message: str,
    user_id: str | None = None,
) -> RuntimeState:
    """Create the minimal structured state for a new runtime run."""
    return RuntimeState(
        run_id=run_id,
        conversation_id=conversation_id,
        user_id=user_id,
        input_message=input_message,
        current_stage=V1_STAGE_NAMES[0],
        completed_stages=[],
        stage_outputs={},
        pending_approval=None,
        public_messages=[],
        private_notes=[],
        errors=[],
    )


def mark_stage_started(state: RuntimeState, stage: str) -> RuntimeState:
    """Return a state copy with the current stage updated."""
    _require_valid_stage(stage)
    updated = dict(state)
    updated["current_stage"] = stage
    return RuntimeState(**updated)


def record_stage_output(
    state: RuntimeState,
    *,
    stage: str,
    output: dict[str, Any],
) -> RuntimeState:
    """Return a state copy containing a completed stage output."""
    _require_valid_stage(stage)

    completed_stages = list(state.get("completed_stages", []))
    if stage not in completed_stages:
        completed_stages.append(stage)

    stage_outputs = dict(state.get("stage_outputs", {}))
    stage_outputs[stage] = dict(output)

    updated = dict(state)
    updated["completed_stages"] = completed_stages
    updated["stage_outputs"] = stage_outputs
    return RuntimeState(**updated)


def record_runtime_error(
    state: RuntimeState,
    *,
    error: dict[str, Any],
) -> RuntimeState:
    """Return a state copy with a structured runtime error appended."""
    errors = list(state.get("errors", []))
    errors.append(dict(error))
    updated = dict(state)
    updated["errors"] = errors
    return RuntimeState(**updated)


def _require_valid_stage(stage: str) -> None:
    if not is_valid_stage(stage):
        raise ValueError(f"Unknown runtime stage: {stage}")
