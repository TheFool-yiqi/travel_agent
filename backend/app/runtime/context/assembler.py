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
