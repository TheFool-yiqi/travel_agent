"""Route, transport, and activity domain planner."""

from __future__ import annotations

from app.runtime.planning._helpers import (
    assemble_agent_context,
    cards_by_type,
    destination_from_state,
    evidence_card_ids,
    evidence_cards_from_context,
    sufficiency_assumptions,
    travel_days_from_state,
    weather_risks_from_context,
)
from app.runtime.planning.schemas import PlanProposal
from app.runtime.state import RuntimeState


class RouteTransportActivityPlanner:
    agent_name = "route_transport_activity_planner"

    def plan(self, state: RuntimeState) -> PlanProposal:
        agent_context = assemble_agent_context(self.agent_name, state)
        destination = destination_from_state(state) or "待确认目的地"
        travel_days = travel_days_from_state(state)
        cards = evidence_cards_from_context(agent_context)
        route_cards = cards_by_type(cards, "route_relation")
        activity_cards = cards_by_type(cards, "time_intensity")

        activity_sequence: list[str] = []
        for card in route_cards + activity_cards:
            claim = str(card.get("claim") or "").strip()
            if claim:
                activity_sequence.append(claim)

        daily_route = [
            {
                "day_number": day_number,
                "focus": activity_sequence[(day_number - 1) % len(activity_sequence)]
                if activity_sequence
                else f"{destination} 市区机动",
            }
            for day_number in range(1, travel_days + 1)
        ]

        transport_risks = weather_risks_from_context(agent_context)
        assumptions = sufficiency_assumptions(state)
        if not route_cards and not activity_cards:
            assumptions.append("缺少路线/强度证据，交通与活动安排基于通用低强度假设")

        return PlanProposal(
            agent_name=self.agent_name,
            summary=f"{destination} 路线与活动安排",
            recommendations=activity_sequence[:travel_days] or [f"{destination} 市内轻松游览"],
            risks=transport_risks,
            assumptions=assumptions,
            evidence_card_ids=evidence_card_ids(route_cards + activity_cards),
            confidence=0.8 if activity_sequence else 0.5,
            detail={
                "daily_route": daily_route,
                "activity_sequence": activity_sequence,
                "local_transfer_assumptions": [
                    "市内以地铁/打车为主，具体班次需现场确认",
                ],
                "transport_risks": transport_risks,
                "intensity_notes": ["整体按低强度安排，预留机动时间"],
            },
        )
