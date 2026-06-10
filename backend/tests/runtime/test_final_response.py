"""Final response and order service tests."""

from __future__ import annotations

import re

from app.runtime.finalization.final_response import FinalResponseGenerator
from app.runtime.finalization.order_service import OrderService
from app.runtime.planning.schemas import ItineraryDraft


def test_order_service_generates_order_prefix() -> None:
    order_id = OrderService.generate_order_id()
    assert re.match(r"^ORDER-[0-9A-F]{8}$", order_id)


def test_final_response_only_uses_itinerary_draft_facts() -> None:
    draft = ItineraryDraft(
        destination="成都",
        travel_days=3,
        summary="成都 3天低强度草案",
        assumptions=["证据不足假设"],
        days=[{"day_number": 1, "theme": "文化游"}],
    )

    result = FinalResponseGenerator().build(draft, order_id="ORDER-TEST1234")

    assert "ORDER-TEST1234" in result.final_message
    assert "成都" in result.final_message
    assert "3" in result.final_message
    assert "证据不足假设" in result.final_message
    assert "故宫" not in result.final_message
