"""Persist PlanningRuntime state in travel session extra_info."""

from __future__ import annotations

from typing import Any

from app.runtime.manifest import V1_STAGE_NAMES
from app.runtime.state import RuntimeState, create_initial_runtime_state

RUNTIME_STATE_KEY = "planning_runtime"


def should_reset_runtime_state(state: RuntimeState) -> bool:
    """Return whether the next user turn should start a fresh runtime run."""
    if state.get("awaiting_user"):
        return False
    if state.get("errors"):
        return True
    completed = list(state.get("completed_stages") or [])
    if "finalize" in completed:
        return True
    return bool(state.get("finalization_result") or state.get("order_id"))


def runtime_state_to_session_payload(state: RuntimeState) -> dict[str, Any]:
    """Serialize RuntimeState for JSON storage in travel_sessions.extra_info."""
    return dict(state)


def runtime_state_from_session_payload(payload: dict[str, Any]) -> RuntimeState:
    """Restore RuntimeState from session extra_info payload."""
    return RuntimeState(**payload)


def load_runtime_state_from_session(
    extra_info: dict[str, Any] | None,
    *,
    run_id: str,
    conversation_id: str,
    user_id: str | None,
    input_message: str,
) -> RuntimeState:
    """Load persisted runtime state or create a new run."""
    raw = (extra_info or {}).get(RUNTIME_STATE_KEY)
    if isinstance(raw, dict) and raw.get("conversation_id") == conversation_id:
        restored = runtime_state_from_session_payload(raw)
        if not should_reset_runtime_state(restored):
            return RuntimeState(
                **{
                    **restored,
                    "input_message": input_message,
                    "user_id": user_id or restored.get("user_id"),
                },
            )

    return create_initial_runtime_state(
        run_id=run_id,
        conversation_id=conversation_id,
        input_message=input_message,
        user_id=user_id,
    )


def prepare_runtime_turn(
    state: RuntimeState,
    *,
    input_message: str,
    user_message_record: dict[str, str],
) -> RuntimeState:
    """Apply per-turn input updates before executing PlanningRuntime."""
    public_messages = list(state.get("public_messages") or [])
    public_messages.append(user_message_record)
    return RuntimeState(
        **{
            **state,
            "input_message": input_message,
            "public_messages": public_messages,
        },
    )


def append_assistant_public_message(
    state: RuntimeState,
    *,
    content: str,
) -> RuntimeState:
    if not content.strip():
        return state
    public_messages = list(state.get("public_messages") or [])
    public_messages.append({"role": "assistant", "content": content.strip()})
    return RuntimeState(**{**state, "public_messages": public_messages})


def resume_stage_index(state: RuntimeState) -> int:
    """Return the V1 stage index to resume from for this turn."""
    if state.get("awaiting_user") and state.get("current_stage") in V1_STAGE_NAMES:
        return V1_STAGE_NAMES.index(str(state["current_stage"]))
    return 0
