"""Dynamic agent context assembly with visibility enforcement."""

from __future__ import annotations

from typing import Any

from app.runtime.collect.schemas import PlanningNeed
from app.runtime.context.schemas import BaseContext
from app.runtime.context.specs import (
    COLLECT_CONTEXT_KEY,
    ContextSpec,
    FORBIDDEN_CONTEXT_KEYS,
    get_context_spec,
    is_formal_planning_agent,
)
from app.runtime.state import RuntimeState


class ContextAssembler:
    """Build agent-specific context views from RuntimeState structured facts."""

    def assemble(self, agent_name: str, state: RuntimeState) -> dict[str, Any]:
        spec = get_context_spec(agent_name)
        if is_formal_planning_agent(agent_name):
            self._reject_raw_collect_context_access(state)

        agent_context: dict[str, Any] = {"agent_name": agent_name}
        if COLLECT_CONTEXT_KEY in spec.allowed_sections:
            collect_context = state.get("collect_context")
            if collect_context is not None:
                agent_context[COLLECT_CONTEXT_KEY] = dict(collect_context)

        planning_need = _load_planning_need(state)
        base_context = _load_base_context(state)

        if "planning_need" in spec.allowed_sections and planning_need is not None:
            agent_context["planning_need"] = planning_need.to_runtime_dict()

        if base_context is not None:
            if "planning_need_summary" in spec.allowed_sections:
                agent_context["planning_need_summary"] = dict(
                    base_context.planning_need_summary,
                )
            if "session_facts" in spec.allowed_sections:
                agent_context["session_facts"] = list(base_context.session_facts)
            if "memory_snippets" in spec.allowed_sections:
                agent_context["memory_snippets"] = list(base_context.memory_snippets)
            if "decision_snippets" in spec.allowed_sections:
                agent_context["decision_snippets"] = list(base_context.decision_snippets)

        if "preferences" in spec.allowed_sections and planning_need is not None:
            agent_context["preferences"] = list(planning_need.preferences)

        if "constraints" in spec.allowed_sections and planning_need is not None:
            agent_context["constraints"] = list(planning_need.constraints)

        if "evidence_cards" in spec.allowed_sections:
            evidence_context = state.get("evidence_context")
            if evidence_context is not None:
                agent_context["evidence_cards"] = _build_evidence_cards_view(
                    evidence_context,
                )

        if "weather_summary" in spec.allowed_sections:
            tool_context = state.get("tool_context")
            if tool_context is not None:
                agent_context["weather_summary"] = _build_weather_summary_view(
                    tool_context,
                )

        if "itinerary_summary" in spec.allowed_sections:
            itinerary_draft = state.get("itinerary_draft")
            if itinerary_draft is not None:
                agent_context["itinerary_summary"] = _build_itinerary_summary_view(
                    itinerary_draft,
                )

        if "sufficiency_summary" in spec.allowed_sections:
            sufficiency_result = state.get("sufficiency_result")
            if sufficiency_result is not None:
                agent_context["sufficiency_summary"] = _build_sufficiency_summary_view(
                    sufficiency_result,
                )

        self._validate_agent_context(agent_context, spec)
        return agent_context

    @staticmethod
    def _reject_raw_collect_context_access(state: RuntimeState) -> None:
        if state.get("collect_context") is None:
            return

    @staticmethod
    def _validate_agent_context(agent_context: dict[str, Any], spec: ContextSpec) -> None:
        for key in agent_context:
            if key == "agent_name" or key in spec.allowed_sections:
                continue
            if key in spec.denied_sections or key in FORBIDDEN_CONTEXT_KEYS:
                raise ValueError(f"Agent context contains denied section: {key}")

        if is_formal_planning_agent(spec.agent_name):
            if COLLECT_CONTEXT_KEY in agent_context:
                raise ValueError("Formal planning agents must not receive collect_context")

        _assert_no_prompt_keys(agent_context)


def _load_planning_need(state: RuntimeState) -> PlanningNeed | None:
    raw = state.get("planning_need")
    if not raw:
        return None
    return PlanningNeed.from_runtime_dict(raw)


def _load_base_context(state: RuntimeState) -> BaseContext | None:
    raw = state.get("base_context")
    if not raw:
        return None
    return BaseContext.from_runtime_dict(raw)


_EVIDENCE_CARD_SUMMARY_FIELDS = (
    "id",
    "claim",
    "evidence_type",
    "city",
    "entities",
    "applies_to",
    "time_hint",
    "intensity",
)


def _build_evidence_cards_view(evidence_context: dict[str, Any]) -> dict[str, Any]:
    """Expose card ids and claim summaries without raw retrieval traces."""
    cards: list[dict[str, Any]] = []
    for card in evidence_context.get("cards") or []:
        if not isinstance(card, dict):
            continue
        cards.append(
            {
                field: card[field]
                for field in _EVIDENCE_CARD_SUMMARY_FIELDS
                if field in card
            },
        )
    return {
        "card_ids": list(evidence_context.get("card_ids") or []),
        "cards": cards,
    }


_WEATHER_SUMMARY_FIELDS = (
    "status",
    "destination",
    "date_range",
    "summary",
    "risks",
)


def _build_weather_summary_view(tool_context: dict[str, Any]) -> dict[str, Any]:
    """Expose trimmed weather for planners; not raw markdown or tool warnings."""
    weather = tool_context.get("weather")
    if not isinstance(weather, dict):
        return {"status": "unavailable"}
    return {
        field: weather[field]
        for field in _WEATHER_SUMMARY_FIELDS
        if field in weather
    }


def _build_itinerary_summary_view(itinerary_draft: dict[str, Any]) -> dict[str, Any]:
    return {
        "destination": itinerary_draft.get("destination"),
        "travel_days": itinerary_draft.get("travel_days"),
        "summary": itinerary_draft.get("summary") or "",
        "assumptions": list(itinerary_draft.get("assumptions") or []),
        "day_count": len(itinerary_draft.get("days") or []),
        "evidence_card_ids": list(itinerary_draft.get("evidence_card_ids") or []),
    }


def _build_sufficiency_summary_view(sufficiency_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "is_sufficient": sufficiency_result.get("is_sufficient"),
        "score": sufficiency_result.get("score"),
        "missing_tags": list(sufficiency_result.get("missing_tags") or []),
        "missing_evidence_types": list(
            sufficiency_result.get("missing_evidence_types") or [],
        ),
        "suggested_action": sufficiency_result.get("suggested_action"),
    }


def _assert_no_prompt_keys(value: Any, *, path: str = "") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            current_path = f"{path}.{key}" if path else str(key)
            lowered = str(key).lower()
            if lowered in {"prompt", "assembled_context", "raw_messages"}:
                raise ValueError(f"Agent context must not contain prompt-like key: {current_path}")
            _assert_no_prompt_keys(nested, path=current_path)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _assert_no_prompt_keys(nested, path=f"{path}[{index}]")
