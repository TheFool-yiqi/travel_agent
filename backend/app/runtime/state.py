"""PlanningRuntime state contract and update helpers."""

from __future__ import annotations

import copy
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
    collect_context: dict[str, Any] | None
    planning_need: dict[str, Any] | None
    base_context: dict[str, Any] | None
    awaiting_user: bool
    collect_turn_count: int
    evidence_context: dict[str, Any] | None
    sufficiency_result: dict[str, Any] | None
    tool_context: dict[str, Any] | None
    plan_proposals: list[dict[str, Any]] | None
    itinerary_draft: dict[str, Any] | None
    quality_report: dict[str, Any] | None
    revision_count: int
    approval_status: str | None
    order_id: str | None
    finalization_result: dict[str, Any] | None


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
        collect_context=None,
        planning_need=None,
        base_context=None,
        awaiting_user=False,
        collect_turn_count=0,
        evidence_context=None,
        sufficiency_result=None,
        tool_context=None,
        plan_proposals=None,
        itinerary_draft=None,
        quality_report=None,
        revision_count=0,
        approval_status=None,
        order_id=None,
        finalization_result=None,
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


def set_collect_context(
    state: RuntimeState,
    collect_context: dict[str, Any] | None,
) -> RuntimeState:
    """Return a state copy with collect-only context updated."""
    updated = dict(state)
    updated["collect_context"] = _copy_optional_dict(collect_context)
    return RuntimeState(**updated)


def set_planning_need(
    state: RuntimeState,
    planning_need: dict[str, Any] | None,
) -> RuntimeState:
    """Return a state copy with the formal planning input contract."""
    updated = dict(state)
    updated["planning_need"] = _copy_optional_dict(planning_need)
    return RuntimeState(**updated)


def set_base_context(
    state: RuntimeState,
    base_context: dict[str, Any] | None,
) -> RuntimeState:
    """Return a state copy with shared planning background context."""
    updated = dict(state)
    updated["base_context"] = _copy_optional_dict(base_context)
    return RuntimeState(**updated)


def record_collect_waiting(state: RuntimeState) -> RuntimeState:
    """Return a state copy that pauses the runtime until the next user turn."""
    updated = dict(state)
    updated["awaiting_user"] = True
    return RuntimeState(**updated)


def set_evidence_context(
    state: RuntimeState,
    evidence_context: dict[str, Any] | None,
) -> RuntimeState:
    """Return a state copy with retrieved evidence context."""
    updated = dict(state)
    updated["evidence_context"] = _copy_optional_dict(evidence_context)
    return RuntimeState(**updated)


def set_sufficiency_result(
    state: RuntimeState,
    sufficiency_result: dict[str, Any] | None,
) -> RuntimeState:
    """Return a state copy with evidence sufficiency evaluation."""
    updated = dict(state)
    updated["sufficiency_result"] = _copy_optional_dict(sufficiency_result)
    return RuntimeState(**updated)


def set_tool_context(
    state: RuntimeState,
    tool_context: dict[str, Any] | None,
) -> RuntimeState:
    """Return a state copy with tool enrichment context."""
    updated = dict(state)
    updated["tool_context"] = _copy_optional_dict(tool_context)
    return RuntimeState(**updated)


def set_plan_proposals(
    state: RuntimeState,
    plan_proposals: list[dict[str, Any]] | None,
) -> RuntimeState:
    """Return a state copy with domain planner proposals."""
    updated = dict(state)
    if plan_proposals is None:
        updated["plan_proposals"] = None
    else:
        updated["plan_proposals"] = copy.deepcopy(plan_proposals)
    return RuntimeState(**updated)


def set_itinerary_draft(
    state: RuntimeState,
    itinerary_draft: dict[str, Any] | None,
) -> RuntimeState:
    """Return a state copy with integrated itinerary draft."""
    updated = dict(state)
    updated["itinerary_draft"] = _copy_optional_dict(itinerary_draft)
    return RuntimeState(**updated)


def set_quality_report(
    state: RuntimeState,
    quality_report: dict[str, Any] | None,
) -> RuntimeState:
    """Return a state copy with quality verification report."""
    updated = dict(state)
    updated["quality_report"] = _copy_optional_dict(quality_report)
    return RuntimeState(**updated)


def increment_revision_count(state: RuntimeState) -> RuntimeState:
    """Return a state copy with revision_count incremented by one."""
    updated = dict(state)
    updated["revision_count"] = int(updated.get("revision_count") or 0) + 1
    return RuntimeState(**updated)


def set_pending_approval(
    state: RuntimeState,
    pending_approval: dict[str, Any] | None,
) -> RuntimeState:
    updated = dict(state)
    updated["pending_approval"] = _copy_optional_dict(pending_approval)
    return RuntimeState(**updated)


def clear_pending_approval(state: RuntimeState) -> RuntimeState:
    updated = dict(state)
    updated["pending_approval"] = None
    return RuntimeState(**updated)


def set_approval_status(
    state: RuntimeState,
    approval_status: str | None,
) -> RuntimeState:
    updated = dict(state)
    updated["approval_status"] = approval_status
    return RuntimeState(**updated)


def set_order_id(state: RuntimeState, order_id: str | None) -> RuntimeState:
    updated = dict(state)
    updated["order_id"] = order_id
    return RuntimeState(**updated)


def set_finalization_result(
    state: RuntimeState,
    finalization_result: dict[str, Any] | None,
) -> RuntimeState:
    updated = dict(state)
    updated["finalization_result"] = _copy_optional_dict(finalization_result)
    return RuntimeState(**updated)


def _copy_optional_dict(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return copy.deepcopy(value)


def _require_valid_stage(stage: str) -> None:
    if not is_valid_stage(stage):
        raise ValueError(f"Unknown runtime stage: {stage}")
