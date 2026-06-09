"""Collect turn orchestration for PlanningRuntime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.graph.templates.budget_tiers import apply_budget_tier_to_fields, apply_party_from_dialogue
from app.graph.validators.requirements import (
    sanitize_budget,
    sanitize_destination,
    sanitize_travel_styles,
)
from app.runtime.collect.conversation_policy import choose_public_reply
from app.runtime.collect.greeting import GreetingPolicy, GreetingResponder
from app.runtime.collect.planning_input import (
    compile_planning_need,
    detect_explicit_draft_request,
    detect_user_confirmed,
    validate_planning_input,
)
from app.runtime.collect.readiness import evaluate_readiness
from app.runtime.collect.schemas import CollectContext, collect_context_from_runtime_dict, collect_context_to_runtime_dict
from app.runtime.semantic.collection_frame import CollectSemanticLayer
from app.runtime.state import RuntimeState
from app.tools.holiday_calendar import apply_holiday_date_to_fields

CollectTurnStatus = Literal["continue", "waiting", "ready"]


@dataclass(frozen=True)
class CollectTurnResult:
    status: CollectTurnStatus
    public_reply: str
    collect_context: dict[str, Any]
    planning_need: dict[str, Any] | None = None


class CollectRuntime:
    """Single-turn collect orchestrator; semantic rules run before any LLM extraction."""

    def __init__(self, *, semantic_layer: type[CollectSemanticLayer] = CollectSemanticLayer) -> None:
        self._semantic = semantic_layer

    async def process_turn(
        self,
        state: RuntimeState,
        *,
        user_message: str | None = None,
    ) -> CollectTurnResult:
        message = (user_message if user_message is not None else state.get("input_message", "")).strip()
        collect_context = _load_collect_context(state)
        conversation_state = dict(collect_context.conversation_state)
        trip_spec = dict(collect_context.trip_spec)
        has_prior_assistant = bool(conversation_state.get("has_prior_assistant_message"))

        if GreetingPolicy.should_greet(
            user_message=message,
            has_prior_assistant_message=has_prior_assistant,
        ):
            reply = GreetingResponder.build_reply(already_greeted=has_prior_assistant)
            updated_context = _updated_collect_context(
                collect_context,
                trip_spec=trip_spec,
                conversation_state={
                    **conversation_state,
                    "has_prior_assistant_message": True,
                    "last_turn": "greeting",
                },
                readiness_state={"status": "continue_collect", "reason": "greeting_only"},
            )
            return CollectTurnResult(
                status="waiting",
                public_reply=reply,
                collect_context=collect_context_to_runtime_dict(updated_context),
            )

        semantic_state = _semantic_state(collect_context)
        messages = _messages_from_state(state, message)
        extraction, frame = self._semantic.rule_extract(messages, trip_spec, semantic_state)
        trip_spec = _merge_trip_spec(trip_spec, extraction.model_dump(exclude_none=True))

        dialogue_text = self._semantic.dialogue_text(messages)
        trip_spec = apply_holiday_date_to_fields(trip_spec, dialogue_text)
        trip_spec = apply_party_from_dialogue(trip_spec, dialogue_text)
        trip_spec = apply_budget_tier_to_fields(trip_spec, dialogue_text)

        trip_spec, semantic_reply, pending_update = self._semantic.apply_frame(
            trip_spec,
            semantic_state,
            frame,
        )
        trip_spec = sanitize_travel_styles(trip_spec, dialogue_text=dialogue_text)
        trip_spec = sanitize_budget(trip_spec, dialogue_text=dialogue_text)
        trip_spec = sanitize_destination(
            trip_spec,
            dialogue_text=dialogue_text,
            pending_clarification=pending_update or collect_context.pending_clarification,
        )

        pending_clarification = collect_context.pending_clarification
        if pending_update is not None:
            pending_clarification = pending_update or None

        user_confirmed = detect_user_confirmed(
            user_message=message,
            conversation_state=conversation_state,
        )
        explicit_draft_request = detect_explicit_draft_request(message)
        validation_errors = validate_planning_input(trip_spec, dialogue_text=dialogue_text)

        discovery_state = dict(collect_context.discovery_state)
        has_unconfirmed_discovery = bool(
            discovery_state.get("proposed") and not discovery_state.get("confirmed"),
        )
        readiness_status, readiness_meta = evaluate_readiness(
            trip_spec,
            user_confirmed=user_confirmed,
            dialogue_text=dialogue_text,
            has_unconfirmed_discovery=has_unconfirmed_discovery,
        )

        public_reply = choose_public_reply(
            trip_spec=trip_spec,
            readiness_status=readiness_status,
            dialogue_text=dialogue_text,
            semantic_reply=semantic_reply,
            validation_errors=validation_errors,
        )

        updated_conversation_state = {
            **conversation_state,
            "user_confirmed": user_confirmed,
            "explicit_draft_request": explicit_draft_request,
            "has_prior_assistant_message": True,
            "last_turn": readiness_status,
        }
        updated_context = _updated_collect_context(
            collect_context,
            trip_spec=trip_spec,
            conversation_state=updated_conversation_state,
            discovery_state=discovery_state,
            readiness_state={"status": readiness_status, **readiness_meta},
            pending_clarification=pending_clarification,
        )

        if readiness_status == "ready_for_planning" and not validation_errors:
            planning_need = compile_planning_need(
                trip_spec,
                user_confirmed=user_confirmed,
                explicit_draft_request=explicit_draft_request,
            )
            return CollectTurnResult(
                status="ready",
                public_reply=public_reply,
                collect_context=collect_context_to_runtime_dict(updated_context),
                planning_need=planning_need.to_runtime_dict(),
            )

        return CollectTurnResult(
            status="waiting",
            public_reply=public_reply,
            collect_context=collect_context_to_runtime_dict(updated_context),
        )


def _load_collect_context(state: RuntimeState) -> CollectContext:
    raw = state.get("collect_context")
    if raw:
        return collect_context_from_runtime_dict(raw)
    return CollectContext()


def _updated_collect_context(
    current: CollectContext,
    *,
    trip_spec: dict[str, Any],
    conversation_state: dict[str, Any],
    discovery_state: dict[str, Any] | None = None,
    readiness_state: dict[str, Any] | None = None,
    pending_clarification: dict[str, Any] | None = None,
) -> CollectContext:
    return CollectContext(
        trip_spec=trip_spec,
        conversation_state=conversation_state,
        discovery_state=discovery_state if discovery_state is not None else current.discovery_state,
        readiness_state=readiness_state if readiness_state is not None else current.readiness_state,
        pending_clarification=pending_clarification,
        rejected_assumptions=list(current.rejected_assumptions),
    )


def _semantic_state(collect_context: CollectContext) -> dict[str, Any]:
    return {
        "pending_clarification": collect_context.pending_clarification,
        **collect_context.trip_spec,
    }


def _messages_from_state(state: RuntimeState, user_message: str) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    for item in state.get("public_messages") or []:
        role = item.get("role")
        content = str(item.get("content", ""))
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    if user_message:
        messages.append(HumanMessage(content=user_message))
    return messages


def _merge_trip_spec(trip_spec: dict[str, Any], extraction: dict[str, Any]) -> dict[str, Any]:
    merged = dict(trip_spec)
    for key, value in extraction.items():
        if value is not None and value != "" and value != []:
            merged[key] = value
    return merged
