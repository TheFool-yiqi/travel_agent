"""分步引导顺序测试"""

from app.graph.greeting import build_greeting_reply
from app.graph.templates.collect_followup import render_collect_followup
from app.graph.templates.collect_guidance import next_guidance_step


def test_greeting_only_asks_destination():
    reply = build_greeting_reply()
    assert "去哪里" in reply or "去哪" in reply
    assert "出发" not in reply
    assert "端午" not in reply


def test_guidance_order_destination_first():
    assert next_guidance_step({}) == "destination"
    assert next_guidance_step({"destination": "成都"}) == "departure_city"
    assert next_guidance_step({"destination": "成都", "departure_city": "上海"}) == "departure_date"


def test_followup_shanghai_only_asks_destination():
    text = render_collect_followup({"departure_city": "上海"})
    assert "去哪" in text or "目的地" in text or "成都" in text
    assert "端午" not in text


def test_followup_with_destination_asks_departure_city():
    text = render_collect_followup({"destination": "成都"})
    assert "出发" in text
    assert "端午" not in text


def test_needs_guidance_followup_false_when_awaiting_confirmation():
    from app.graph.templates.collect_guidance import needs_guidance_followup

    fields = {
        "destination": "北京",
        "departure_city": "上海",
        "departure_date": "2026-06-19",
        "travel_days": 3,
        "adult_count": 1,
        "children_count": 0,
        "party_confirmed": True,
        "budget_min": 800,
        "budget_max": 2000,
    }
    assert needs_guidance_followup(fields, awaiting_confirmation=True) is False


def test_needs_guidance_followup_false_when_done():
    from app.graph.templates.collect_guidance import needs_guidance_followup

    fields = {
        "destination": "北京",
        "departure_city": "上海",
        "departure_date": "2026-06-19",
        "travel_days": 3,
        "adult_count": 1,
        "children_count": 0,
        "party_confirmed": True,
        "budget_min": 800,
        "budget_max": 2000,
    }
    assert needs_guidance_followup(fields) is False
