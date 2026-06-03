"""travel_styles 防幻觉校验测试"""

from app.graph.validators.requirements import (
    explicit_travel_styles_in_dialogue,
    sanitize_travel_styles,
)


def test_sanitize_removes_inferred_culture_after_budget_tier():
    fields = {
        "departure_city": "上海",
        "budget_min": 800,
        "budget_max": 2000,
        "travel_styles": ["culture"],
    }
    dialogue = "\n".join(
        [
            "用户: 成都",
            "助手: 好的",
            "用户: 上海",
            "用户: 3天",
            "用户: 2大1小",
            "用户: 穷游党",
        ],
    )
    sanitized = sanitize_travel_styles(fields, dialogue_text=dialogue)
    assert "travel_styles" not in sanitized


def test_sanitize_keeps_explicit_travel_style():
    fields = {
        "departure_city": "上海",
        "travel_styles": ["culture", "food"],
    }
    dialogue = "用户: 我想逛人文博物馆，顺便吃吃喝喝"
    sanitized = sanitize_travel_styles(fields, dialogue_text=dialogue)
    assert sanitized.get("travel_styles") == ["culture", "food"]


def test_explicit_travel_styles_ignore_assistant_prompts():
    dialogue = "\n".join(
        [
            "助手: 更想躺平放松、逛人文，还是吃吃喝喝？",
            "用户: 穷游党",
        ],
    )
    assert explicit_travel_styles_in_dialogue(dialogue) == []
