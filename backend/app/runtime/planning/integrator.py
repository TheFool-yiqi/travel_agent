"""Itinerary integrator for domain planning proposals."""

from __future__ import annotations

from app.runtime.planning._helpers import destination_from_state, travel_days_from_state
from app.runtime.planning.schemas import ItineraryDraft, PlanProposal
from app.runtime.state import RuntimeState


class ItineraryIntegrator:
    """Merge PlanProposal outputs into a structured itinerary draft."""

    def integrate(
        self,
        state: RuntimeState,
        proposals: list[PlanProposal],
    ) -> ItineraryDraft:
        destination = destination_from_state(state) or "待确认目的地"
        travel_days = travel_days_from_state(state)

        by_agent = {proposal.agent_name: proposal for proposal in proposals}
        destination_proposal = by_agent.get("destination_planner")
        route_proposal = by_agent.get("route_transport_activity_planner")
        stay_food_proposal = by_agent.get("stay_food_planner")

        route_detail = (route_proposal.detail if route_proposal else {}) or {}
        daily_route = route_detail.get("daily_route") or []
        activity_sequence = route_detail.get("activity_sequence") or []
        food_highlights = (
            (stay_food_proposal.detail if stay_food_proposal else {}) or {}
        ).get("food_highlights") or []

        days: list[dict] = []
        for day_number in range(1, travel_days + 1):
            route_focus = ""
            if daily_route and len(daily_route) >= day_number:
                route_focus = str(daily_route[day_number - 1].get("focus") or "")
            elif activity_sequence:
                route_focus = activity_sequence[(day_number - 1) % len(activity_sequence)]
            else:
                route_focus = f"{destination} 轻松游览"

            meal = (
                str(food_highlights[(day_number - 1) % len(food_highlights)])
                if food_highlights
                else f"{destination} 本地餐饮"
            )
            days.append(
                {
                    "day_number": day_number,
                    "theme": route_focus[:40] or f"第{day_number}天",
                    "activities": [
                        route_focus,
                        "下午预留机动或休息",
                    ],
                    "meals": {"lunch": "就近简餐", "dinner": meal},
                    "accommodation": f"{destination} 交通便利区域",
                    "plan_b": "如遇天气不佳，改为室内文化或美食体验",
                },
            )

        assumptions: list[str] = []
        evidence_card_ids: list[str] = []
        integration_notes: list[str] = []
        for proposal in proposals:
            assumptions.extend(proposal.assumptions)
            evidence_card_ids.extend(proposal.evidence_card_ids)
            if proposal.risks:
                integration_notes.extend(
                    f"{proposal.agent_name}: {risk}" for risk in proposal.risks
                )

        summary = (
            f"{destination} {travel_days}天行程草案："
            + (destination_proposal.summary if destination_proposal else "已整合领域建议")
        )

        return ItineraryDraft(
            destination=destination,
            travel_days=travel_days,
            days=days,
            budget={
                "total": None,
                "note": "V1 草案不含精确预算，待后续验证阶段补充",
            },
            summary=summary,
            assumptions=list(dict.fromkeys(assumptions)),
            evidence_card_ids=list(dict.fromkeys(evidence_card_ids)),
            integration_notes=integration_notes,
        )
