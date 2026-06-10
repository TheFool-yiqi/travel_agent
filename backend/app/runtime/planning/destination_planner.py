"""Destination domain planner."""

from __future__ import annotations

from app.runtime.planning._helpers import (
    assemble_agent_context,
    destination_from_state,
    evidence_card_ids,
    evidence_cards_from_context,
    sufficiency_assumptions,
    travel_days_from_state,
)
from app.runtime.planning.schemas import PlanProposal
from app.runtime.state import RuntimeState


class DestinationPlanner:
    agent_name = "destination_planner"

    def plan(self, state: RuntimeState) -> PlanProposal:
        agent_context = assemble_agent_context(self.agent_name, state)
        destination = destination_from_state(state) or "待确认目的地"
        travel_days = travel_days_from_state(state)
        cards = evidence_cards_from_context(agent_context)
        card_ids = evidence_card_ids(cards)

        recommendations = [
            f"以{destination}为核心目的地，按{travel_days}天低强度节奏组织行程",
        ]
        if cards:
            highlights = [
                entity
                for card in cards
                for entity in (card.get("entities") or [])[:2]
            ]
            if highlights:
                unique = list(dict.fromkeys(str(item) for item in highlights))[:4]
                recommendations.append(f"优先覆盖证据支持的亮点：{'、'.join(unique)}")

        assumptions = sufficiency_assumptions(state)
        if destination == "待确认目的地":
            assumptions.append("目的地尚未完全确认，当前方案基于已收集偏好生成")

        return PlanProposal(
            agent_name=self.agent_name,
            summary=f"{destination} {travel_days}天目的地策略",
            recommendations=recommendations,
            assumptions=assumptions,
            evidence_card_ids=card_ids,
            confidence=0.85 if card_ids else 0.55,
            detail={
                "destination": destination,
                "travel_days": travel_days,
                "focus": "balanced_overview",
            },
        )
