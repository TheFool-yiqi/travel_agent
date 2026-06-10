"""Stay and food domain planner."""

from __future__ import annotations

from app.runtime.planning._helpers import (
    assemble_agent_context,
    cards_by_type,
    destination_from_state,
    evidence_card_ids,
    evidence_cards_from_context,
    sufficiency_assumptions,
)
from app.runtime.planning.schemas import PlanProposal
from app.runtime.state import RuntimeState


class StayFoodPlanner:
    agent_name = "stay_food_planner"

    def plan(self, state: RuntimeState) -> PlanProposal:
        agent_context = assemble_agent_context(self.agent_name, state)
        destination = destination_from_state(state) or "待确认目的地"
        cards = evidence_cards_from_context(agent_context)
        food_cards = cards_by_type(cards, "food_option")

        recommendations = [
            str(card.get("claim")).strip()
            for card in food_cards
            if str(card.get("claim") or "").strip()
        ]
        assumptions = sufficiency_assumptions(state)
        assumptions.append("住宿区域基于市中心便利性假设，未接入实时酒店供给")

        if not recommendations:
            recommendations = [f"{destination} 本地特色餐饮探索（待现场确认具体门店）"]
            assumptions.append("缺少美食证据，餐饮建议为通用假设")

        return PlanProposal(
            agent_name=self.agent_name,
            summary=f"{destination} 住宿与餐饮建议",
            recommendations=recommendations,
            assumptions=assumptions,
            evidence_card_ids=evidence_card_ids(food_cards),
            confidence=0.75 if food_cards else 0.5,
            detail={
                "stay_areas": [f"{destination} 市中心或交通便利区域"],
                "food_highlights": recommendations,
                "meal_notes": ["晚餐可安排美食探索，午餐就近简餐"],
            },
        )
