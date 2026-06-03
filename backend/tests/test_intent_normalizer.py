"""intent_normalizer 测试（P2.1）"""

from app.graph.semantic.intent_normalizer import expand_colloquial_phrases, extract_intent_slots


def test_expand_colloquial_time():
    assert "下周" in expand_colloquial_phrases("下礼拜五走")


def test_expand_colloquial_party():
    assert "2成人1儿童" in expand_colloquial_phrases("一家三口去成都")


def test_extract_party_solo_at_party_step():
    slots = extract_intent_slots("就我一个人", "party", {})
    assert slots.get("adult_count") == 1
    assert slots.get("party_confirmed") is True


def test_extract_budget_tier():
    slots = extract_intent_slots("学生党吧", "budget", {})
    assert slots.get("budget_min") == 800
    assert slots.get("budget_max") == 2000


def test_extract_transport_to_special_needs():
    slots = extract_intent_slots("想坐高铁去", "departure_city", {})
    assert "高铁" in (slots.get("special_needs") or "")


def test_extract_travel_days_range():
    slots = extract_intent_slots("玩个三四天", "travel_days", {})
    assert slots.get("travel_days") in (3, 4)


def test_extract_whole_holiday_duration_from_departure_date():
    fields = {"departure_date": "2026-06-19"}
    for phrase in ("整个假期", "整个小长假", "假期都玩", "放几天玩几天"):
        slots = extract_intent_slots(phrase, "travel_days", fields)
        assert slots.get("travel_days") == 3, phrase


def test_extract_whole_holiday_duration_labor_day():
    fields = {"departure_date": "2026-05-01"}
    slots = extract_intent_slots("整个小长假", "travel_days", fields)
    assert slots.get("travel_days") == 5
