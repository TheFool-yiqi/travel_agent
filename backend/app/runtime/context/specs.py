"""Context visibility specs for Runtime agents and stages."""

from __future__ import annotations

from dataclasses import dataclass

COLLECT_CONTEXT_KEY = "collect_context"
FORBIDDEN_CONTEXT_KEYS = frozenset(
    {
        COLLECT_CONTEXT_KEY,
        "public_messages",
        "private_notes",
        "input_message",
        "prompt",
        "assembled_context",
        "raw_messages",
        "retrieval_trace",
        "evidence_context",
        "tool_context",
    },
)


@dataclass(frozen=True)
class ContextSpec:
    agent_name: str
    allowed_sections: frozenset[str]
    denied_sections: frozenset[str] = FORBIDDEN_CONTEXT_KEYS


V1_CONTEXT_SPECS: dict[str, ContextSpec] = {
    "collect_agent": ContextSpec(
        agent_name="collect_agent",
        allowed_sections=frozenset({COLLECT_CONTEXT_KEY}),
        denied_sections=frozenset(
            {
                "planning_need",
                "base_context",
                "public_messages",
                "private_notes",
                "input_message",
                "prompt",
                "assembled_context",
                "raw_messages",
            },
        ),
    ),
    "destination_planner": ContextSpec(
        agent_name="destination_planner",
        allowed_sections=frozenset(
            {
                "planning_need",
                "planning_need_summary",
                "preferences",
                "constraints",
                "evidence_cards",
            },
        ),
    ),
    "route_transport_activity_planner": ContextSpec(
        agent_name="route_transport_activity_planner",
        allowed_sections=frozenset(
            {
                "planning_need",
                "planning_need_summary",
                "preferences",
                "constraints",
                "session_facts",
                "weather_summary",
            },
        ),
    ),
    "stay_food_planner": ContextSpec(
        agent_name="stay_food_planner",
        allowed_sections=frozenset(
            {
                "planning_need",
                "planning_need_summary",
                "preferences",
                "constraints",
                "session_facts",
            },
        ),
    ),
    "itinerary_integrator": ContextSpec(
        agent_name="itinerary_integrator",
        allowed_sections=frozenset(
            {
                "planning_need",
                "planning_need_summary",
                "preferences",
                "constraints",
                "session_facts",
                "memory_snippets",
                "decision_snippets",
                "weather_summary",
            },
        ),
    ),
    "quality_verifier": ContextSpec(
        agent_name="quality_verifier",
        allowed_sections=frozenset(
            {
                "planning_need",
                "planning_need_summary",
                "preferences",
                "constraints",
                "session_facts",
                "memory_snippets",
                "decision_snippets",
            },
        ),
    ),
}


def get_context_spec(agent_name: str) -> ContextSpec:
    try:
        return V1_CONTEXT_SPECS[agent_name]
    except KeyError as exc:
        raise ValueError(f"Unknown context spec for agent: {agent_name}") from exc


def is_formal_planning_agent(agent_name: str) -> bool:
    return agent_name != "collect_agent"
