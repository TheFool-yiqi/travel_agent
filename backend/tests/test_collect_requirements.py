"""collect_requirements 单元测试（纯函数，不调用 LLM）"""

from app.graph.nodes.collect_requirements import (
    _confirmation_reply,
    build_user_requirement,
    is_requirement_complete,
    merge_extraction,
)
from app.schemas.travel import RequirementExtraction


def test_merge_extraction_prefers_new_values():
    state = {"destination": "杭州", "departure_city": "北京", "travel_days": 3}
    extracted = RequirementExtraction(
        departure_city="上海",
        departure_date="2026-05-01",
        travel_days=5,
        adult_count=2,
        budget_min=3000,
        budget_max=5000,
    )
    merged = merge_extraction(state, extracted)
    assert merged["departure_city"] == "上海"
    assert merged["departure_date"] == "2026-05-01"
    assert merged["travel_days"] == 5
    assert merged["adult_count"] == 2
    assert merged["party_confirmed"] is True
    assert merged["budget_min"] == 3000


def test_merge_extraction_ignores_departure_city_while_collecting_destination():
    state = {}
    extracted = RequirementExtraction(departure_city="成都", destination="成都")
    merged = merge_extraction(state, extracted)
    assert merged.get("departure_city") is None
    assert merged.get("destination") == "成都"


def test_merge_extraction_cross_slot_preserves_destination():
    """TC-REQ-004: 成都→上海→日期 跨槽时 destination 不丢。"""
    state = {"destination": "成都"}
    extracted = RequirementExtraction(departure_city="上海")
    merged = merge_extraction(state, extracted)
    assert merged.get("destination") == "成都"
    assert merged.get("departure_city") == "上海"


def test_merge_extraction_does_not_default_adult_count():
    state = {}
    extracted = RequirementExtraction(departure_city="上海")
    merged = merge_extraction(state, extracted)
    assert "adult_count" not in merged


def test_is_requirement_complete_true():
    fields = {
        "departure_city": "深圳",
        "departure_date": "2026-06-01",
        "travel_days": 4,
        "budget_min": 2000,
        "budget_max": 4000,
        "adult_count": 2,
        "party_confirmed": True,
    }
    assert is_requirement_complete(fields) is True


def test_is_requirement_complete_false_without_party():
    fields = {
        "departure_city": "深圳",
        "departure_date": "2026-06-01",
        "travel_days": 4,
        "budget_min": 2000,
        "budget_max": 4000,
    }
    assert is_requirement_complete(fields) is False


def test_is_requirement_complete_false_missing_budget():
    fields = {
        "departure_city": "深圳",
        "departure_date": "2026-06-01",
        "travel_days": 4,
        "budget_min": None,
        "budget_max": 4000,
    }
    assert is_requirement_complete(fields) is False


def test_is_requirement_complete_false_invalid_date():
    fields = {
        "departure_city": "深圳",
        "departure_date": "2026-13-40",
        "travel_days": 4,
        "budget_min": 2000,
        "budget_max": 4000,
    }
    assert is_requirement_complete(fields) is False


def test_build_user_requirement():
    fields = {
        "departure_city": "成都",
        "departure_date": "2026-07-01",
        "travel_days": 3,
        "adult_count": 2,
        "children_count": 1,
        "budget_min": 3000,
        "budget_max": 6000,
        "travel_styles": ["food", "culture"],
        "destination": "成都",
    }
    req = build_user_requirement(fields)
    assert req.departure_city == "成都"
    assert req.travel_days == 3
    assert req.budget_level == "comfort"
    assert "food" in req.travel_styles


def test_confirmation_reply_does_not_duplicate_summary():
    fields = {
        "departure_city": "上海",
        "departure_date": "2026-06-19",
        "travel_days": 3,
        "adult_count": 1,
        "children_count": 0,
        "party_confirmed": True,
        "budget_min": 800,
        "budget_max": 2000,
        "budget_tier": "穷游党",
    }
    reply = _confirmation_reply(fields)
    assert reply.count("出发城市：上海") == 1
    assert "【当前已确认】" not in reply
    assert "我整理一下您的需求：" in reply


def test_merge_extraction_does_not_infer_travel_styles_from_state_only():
    state = {"travel_styles": ["culture"]}
    extracted = RequirementExtraction(
        departure_city="上海",
        budget_min=800,
        budget_max=2000,
    )
    merged = merge_extraction(state, extracted)
    assert merged.get("travel_styles") == ["culture"]
