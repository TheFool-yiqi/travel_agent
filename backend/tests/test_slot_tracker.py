"""slot_tracker 测试（P1.3）"""

from langchain_core.messages import AIMessage, HumanMessage

from app.graph.semantic.slot_tracker import (
    apply_slot_updates,
    bind_utterance_to_slots,
    compute_missing_slots,
)


def test_compute_missing_slots_destination_first():
    assert compute_missing_slots({}) == [
        "destination",
        "departure_city",
        "departure_date",
        "travel_days",
        "party",
        "budget",
    ]
    assert compute_missing_slots({"destination": "成都"})[0] == "departure_city"


def test_bind_destination_typo_clarify():
    frame = bind_utterance_to_slots("程度", {}, {})
    assert frame.pending_clarification is not None
    assert frame.pending_clarification["candidate"] == "成都"
    assert "成都" in (frame.reply_override or "")


def test_bind_destination_exact():
    frame = bind_utterance_to_slots("成都", {}, {})
    assert frame.slot_updates.get("destination") == "成都"
    assert frame.confidence >= 0.85


def test_bind_departure_city_after_destination():
    fields = {"destination": "成都"}
    frame = bind_utterance_to_slots("上海", fields, {})
    assert frame.slot_updates.get("departure_city") == "上海"


def test_confirm_pending_clarification():
    messages_text = "对"
    state = {
        "pending_clarification": {
            "slot": "destination",
            "candidate": "成都",
            "original": "程度",
        },
    }
    frame = bind_utterance_to_slots(messages_text, {}, state)
    assert frame.slot_updates.get("destination") == "成都"
    assert frame.pending_clarification_cleared is True


def test_bind_budget_amount_ambiguity():
    fields = {
        "destination": "成都",
        "departure_city": "上海",
        "departure_date": "2026-06-19",
        "travel_days": 3,
        "adult_count": 2,
        "children_count": 0,
        "party_confirmed": True,
    }
    frame = bind_utterance_to_slots("5000", fields, {})
    assert frame.pending_clarification is not None
    assert frame.pending_clarification.get("kind") == "budget_scope"
    assert "每人" in (frame.reply_override or "")


def test_apply_slot_updates_clears_wrong_departure():
    fields = {"departure_city": "成都"}
    frame = bind_utterance_to_slots("成都", fields, {})
    frame.slot_updates["destination"] = "成都"
    updated = apply_slot_updates(fields, frame, {})
    assert updated.get("destination") == "成都"
    assert "departure_city" not in updated


def test_user_correction_overrides_pending():
    state = {
        "pending_clarification": {
            "slot": "destination",
            "kind": "city",
            "candidate": "成都",
            "original": "程度",
        },
    }
    frame = bind_utterance_to_slots("不对，是承德", {}, state)
    assert frame.slot_updates.get("destination") == "承德"
    assert frame.pending_clarification_cleared is True
    assert any(c.reason == "user_correction" for c in frame.corrections)


def test_bind_empty_utterance_no_updates():
    frame = bind_utterance_to_slots("", {}, {})
    assert not frame.slot_updates
    assert frame.pending_clarification is None
