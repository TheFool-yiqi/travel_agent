"""slot_sanitizer 测试"""

from app.graph.semantic.frame import SemanticFrame
from app.graph.semantic.slot_sanitizer import sanitize_departure_city_collision
from app.graph.semantic.slot_tracker import bind_utterance_to_slots


def test_sanitize_same_city_after_destination_confirm():
    fields = {"destination": "成都", "departure_city": "成都"}
    frame = SemanticFrame(
        slot_updates={"destination": "成都"},
        pending_clarification_cleared=True,
        guidance_step="destination",
    )
    state = {
        "pending_clarification": {
            "slot": "destination",
            "candidate": "成都",
            "original": "程度",
        },
    }
    result = sanitize_departure_city_collision(fields, state, frame)
    assert result.get("destination") == "成都"
    assert "departure_city" not in result


def test_confirm_typo_asks_departure_city_not_date():
    state = {
        "pending_clarification": {
            "slot": "destination",
            "kind": "city",
            "candidate": "成都",
            "original": "程度",
        },
    }
    fields = {"departure_city": "成都"}  # LLM 误绑
    frame = bind_utterance_to_slots("对", fields, state)
    merged = sanitize_departure_city_collision(
        {**fields, **frame.slot_updates},
        state=state,
        frame=frame,
    )
    assert merged.get("destination") == "成都"
    assert "departure_city" not in merged
    assert "出发" in (frame.reply_override or "")
    assert "什么时候" not in (frame.reply_override or "")
