"""budget 防幻觉校验测试"""

from app.graph.templates.budget_tiers import apply_budget_tier_to_fields, detect_budget_tier_key
from app.graph.templates.collect_followup import render_collect_followup
from app.graph.templates.requirements_summary import render_facts_prefix
from app.graph.validators.requirements import explicit_budget_in_dialogue, sanitize_budget


def test_sanitize_removes_llm_inferred_budget_at_party_step():
    """用户未提预算时不应出现「一般党」。"""
    fields = {
        "departure_city": "上海",
        "departure_date": "2026-06-19",
        "travel_days": 3,
        "destination": "成都",
        "budget_min": 2000,
        "budget_max": 5000,
        "budget_tier": "一般党",
    }
    dialogue = "\n".join(
        [
            "用户: 成都",
            "助手: 好的",
            "用户: 上海",
            "用户: 2026-06-19",
            "用户: 3天",
        ],
    )
    sanitized = sanitize_budget(fields, dialogue_text=dialogue)
    assert "budget_min" not in sanitized
    assert "budget_max" not in sanitized
    assert "budget_tier" not in sanitized


def test_sanitize_keeps_explicit_budget_tier():
    fields = {
        "departure_city": "上海",
        "budget_min": 2000,
        "budget_max": 5000,
        "budget_tier": "一般党",
    }
    dialogue = "用户: 一般党"
    sanitized = sanitize_budget(fields, dialogue_text=dialogue)
    assert sanitized.get("budget_min") == 2000
    assert sanitized.get("budget_tier") == "一般党"


def test_sanitize_keeps_explicit_budget_amount():
    fields = {"budget_min": 3000, "budget_max": 3500}
    dialogue = "用户: 每人5000元"
    sanitized = sanitize_budget(fields, dialogue_text=dialogue)
    assert sanitized.get("budget_min") == 3000


def test_sanitize_ignores_assistant_budget_prompt():
    dialogue = "\n".join(
        [
            "助手: 了解啦，穷游党 / 一般党 / 富有党 您更倾向哪一档？",
            "用户: 2大1小",
        ],
    )
    assert explicit_budget_in_dialogue(dialogue) is False


def test_detect_budget_tier_rejects_ambiguous_general():
    assert detect_budget_tier_key("一般") is None
    assert detect_budget_tier_key("普通") is None
    assert detect_budget_tier_key("适中") is None


def test_apply_budget_tier_ignores_assistant_prompt():
    dialogue = "\n".join(
        [
            "用户: 成都",
            "助手: 穷游党 / 一般党 / 富有党 您更倾向哪一档？",
        ],
    )
    fields = apply_budget_tier_to_fields({}, dialogue)
    assert "budget_min" not in fields


def test_facts_prefix_omits_budget_before_user_provides():
    fields = {
        "departure_city": "上海",
        "departure_date": "2026-06-19",
        "travel_days": 3,
        "destination": "成都",
    }
    dialogue = "\n".join(["用户: 成都", "用户: 上海", "用户: 3天"])
    prefix = render_facts_prefix(fields, dialogue_text=dialogue)
    assert "一般党" not in prefix
    assert "预算" not in prefix


def test_collect_followup_asks_party_not_budget():
    fields = {
        "departure_city": "上海",
        "destination": "成都",
        "departure_date": "2026-06-19",
        "travel_days": 3,
    }
    text = render_collect_followup(fields)
    assert "几位" in text or "成人" in text
    assert "一般党" not in text
