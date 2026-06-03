"""final_response 节点测试（订单生成）。"""

from __future__ import annotations

import re

from app.graph.nodes.final_response import final_response


def test_final_response_generates_order_id() -> None:
    state = {
        "selected_destination": "成都",
        "budget": {"total": 3500.0},
        "itinerary": [{"day_number": 1}],
    }
    result = final_response(state)
    content = result["messages"][0].content
    assert re.search(r"ORDER-[A-F0-9]{8}", content)
    assert result["order_id"].startswith("ORDER-")
    assert len(result["order_id"]) >= 14


def test_final_response_includes_destination_and_budget() -> None:
    state = {
        "selected_destination": "北京",
        "budget": {"total": 5200.5},
    }
    result = final_response(state)
    content = result["messages"][0].content
    assert "北京" in content
    assert "5200.50" in content


def test_final_response_idempotent_when_order_exists() -> None:
    state = {"order_id": "ORDER-EXISTING1"}
    result = final_response(state)
    assert "ORDER-EXISTING1" in result["messages"][0].content
    assert "order_id" not in result or result.get("current_step") == "done"
