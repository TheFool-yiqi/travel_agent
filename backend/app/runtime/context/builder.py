"""Build shared BaseContext from validated planning inputs."""

from __future__ import annotations

from typing import Any

from app.runtime.collect.schemas import PlanningNeed
from app.runtime.context.schemas import BaseContext


def build_base_context_from_planning_need(
    planning_need: PlanningNeed,
    *,
    memory_snippets: list[dict[str, Any]] | None = None,
    decision_snippets: list[dict[str, Any]] | None = None,
) -> BaseContext:
    """Derive BaseContext only from PlanningNeed; never from CollectContext."""
    planning_need_summary: dict[str, Any] = {}
    session_facts: list[dict[str, Any]] = []

    for fact in (
        *planning_need.confirmed_facts,
        *planning_need.derived_facts,
        *planning_need.approved_assumptions,
    ):
        planning_need_summary[fact.field] = fact.value
        session_facts.append(
            {
                "field": fact.field,
                "value": fact.value,
                "fact_type": fact.fact_type,
                "source": fact.source,
            },
        )

    if planning_need.preferences:
        planning_need_summary["preferences"] = list(planning_need.preferences)
    if planning_need.constraints:
        planning_need_summary["constraints"] = list(planning_need.constraints)
    if planning_need.missing_but_accepted_fields:
        planning_need_summary["missing_but_accepted_fields"] = list(
            planning_need.missing_but_accepted_fields,
        )
    if planning_need.risk_flags:
        planning_need_summary["risk_flags"] = list(planning_need.risk_flags)

    return BaseContext(
        planning_need_summary=planning_need_summary,
        session_facts=session_facts,
        memory_snippets=list(memory_snippets or []),
        decision_snippets=list(decision_snippets or []),
    )
