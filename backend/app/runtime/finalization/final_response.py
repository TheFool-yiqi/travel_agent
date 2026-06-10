"""Final user-visible message builder."""

from __future__ import annotations

from app.runtime.finalization.schemas import FinalizationResult
from app.runtime.planning.schemas import ItineraryDraft
from app.runtime.finalization.order_service import OrderService


class FinalResponseGenerator:
    """Build finalize message strictly from itinerary draft facts."""

    def build(
        self,
        itinerary_draft: ItineraryDraft,
        *,
        order_id: str | None = None,
    ) -> FinalizationResult:
        resolved_order_id = order_id or OrderService.generate_order_id()
        budget_note = ""
        if itinerary_draft.budget and itinerary_draft.budget.get("note"):
            budget_note = f"\n预算说明：{itinerary_draft.budget['note']}"

        assumptions = ""
        if itinerary_draft.assumptions:
            assumptions = "\n假设项：\n- " + "\n- ".join(itinerary_draft.assumptions)

        message = (
            f"订单生成成功！\n"
            f"订单号：{resolved_order_id}\n"
            f"目的地：{itinerary_draft.destination}\n"
            f"行程天数：{itinerary_draft.travel_days} 天\n"
            f"行程摘要：{itinerary_draft.summary}"
            f"{budget_note}"
            f"{assumptions}\n"
            f"感谢使用 Travel Agent！"
        )

        return FinalizationResult(
            order_id=resolved_order_id,
            final_message=message,
            destination=itinerary_draft.destination,
            travel_days=itinerary_draft.travel_days,
            persisted=False,
        )
