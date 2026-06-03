"""预算档位与人数确认"""

from app.graph.templates.budget_tiers import (
    apply_budget_tier_to_fields,
    apply_party_from_dialogue,
    detect_budget_tier_key,
    render_budget_tier_question,
    render_party_question,
)
from app.graph.templates.collect_followup import render_collect_followup


def test_budget_tier_detection():
    assert detect_budget_tier_key("穷游党") == "economy"
    assert detect_budget_tier_key("一般党") == "comfort"
    assert detect_budget_tier_key("富有党") == "luxury"
    assert detect_budget_tier_key("一般") is None
    assert detect_budget_tier_key("普通") is None


def test_apply_budget_tier_sets_range():
    fields = apply_budget_tier_to_fields({}, "我想一般党")
    assert fields["budget_min"] == 2000
    assert fields["budget_max"] == 5000
    assert fields["budget_tier"] == "一般党"


def test_apply_party_solo():
    fields = apply_party_from_dialogue({}, "就我一个人")
    assert fields["adult_count"] == 1
    assert fields["children_count"] == 0
    assert fields["party_confirmed"] is True


def test_apply_party_adult_child():
    fields = apply_party_from_dialogue({}, "2大1小")
    assert fields["adult_count"] == 2
    assert fields["children_count"] == 1
    assert fields["party_confirmed"] is True


def test_collect_followup_asks_party_before_budget():
    fields = {
        "departure_city": "上海",
        "destination": "成都",
        "departure_date": "2026-06-19",
        "travel_days": 3,
    }
    text = render_collect_followup(fields)
    assert "几位" in text or "成人" in text
    assert "穷游党" not in text


def test_collect_followup_budget_after_party():
    fields = {
        "departure_city": "上海",
        "destination": "成都",
        "departure_date": "2026-06-19",
        "travel_days": 3,
        "adult_count": 2,
        "children_count": 0,
        "party_confirmed": True,
    }
    text = render_collect_followup(fields)
    assert "穷游党" in text
    assert "一般党" in text
    assert "富有党" in text
    assert "2000-30" not in text


def test_budget_tier_prompt_content():
    prompt = render_budget_tier_question()
    assert "800-2000" in prompt
    assert "5000" in prompt
