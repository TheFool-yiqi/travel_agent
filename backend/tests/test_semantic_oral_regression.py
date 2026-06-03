"""口语/错字/省略表达回归集（P2.5，50+ cases）"""

from __future__ import annotations

import pytest

from app.graph.semantic.intent_normalizer import expand_colloquial_phrases
from app.graph.semantic.normalizer import normalize_text
from app.graph.semantic.slot_tracker import bind_utterance_to_slots


def _check(expected, actual) -> bool:
    if callable(expected):
        return bool(expected(actual))
    return actual == expected


@pytest.mark.parametrize(
    ("utterance", "fields", "check_key", "expected"),
    [
        ("程度", {}, "pending", "成都"),
        ("成都", {}, "destination", "成都"),
        ("杭洲", {}, "destination", "杭州"),
        ("上诲", {}, "destination", "上海"),
        ("三亚", {}, "destination", "三亚"),
        ("成度", {}, "pending", "成都"),
        ("城都", {}, "pending", "成都"),
        ("夏门", {}, "destination", "厦门"),
        ("下门", {}, "pending", "厦门"),
        ("重庆", {}, "destination", "重庆"),
        ("西安", {}, "destination", "西安"),
        ("丽江", {}, "destination", "丽江"),
        ("九寨", {}, "destination", "九寨沟"),
        ("洱海", {}, "destination", "大理"),
        ("华山", {}, "destination", "西安"),
        ("赛里木湖", {}, "destination", "伊犁"),
        ("布达拉宫", {}, "destination", "拉萨"),
        ("故宫", {}, "destination", "北京"),
        ("洪崖洞", {}, "destination", "重庆"),
        ("喀纳斯", {}, "destination", "阿勒泰"),
        ("西藏", {}, "destination", "西藏"),
        ("南疆", {}, "destination", "新疆"),
        ("天堂", {}, "pending_fuzzy", ("天津", "天水")),
        ("千岛湖", {}, "destination", "杭州"),
        ("上海", {"destination": "成都"}, "departure_city", "上海"),
        ("北京", {"destination": "杭州"}, "departure_city", "北京"),
        ("下礼拜五", {"destination": "成都", "departure_city": "上海"}, "departure_date", "date"),
        ("这周末", {"destination": "成都", "departure_city": "上海"}, "departure_date", "date"),
        ("明天", {"destination": "成都", "departure_city": "上海"}, "departure_date", "date"),
        ("后天", {"destination": "成都", "departure_city": "上海"}, "departure_date", "date"),
        ("端午节", {"destination": "成都", "departure_city": "上海"}, "departure_date", "2026-06-19"),
        (
            "玩3天",
            {"destination": "成都", "departure_city": "上海", "departure_date": "2026-06-19"},
            "travel_days",
            3,
        ),
        (
            "5天",
            {"destination": "成都", "departure_city": "上海", "departure_date": "2026-06-19"},
            "travel_days",
            5,
        ),
        (
            "玩个三四天",
            {"destination": "成都", "departure_city": "上海", "departure_date": "2026-06-19"},
            "travel_days",
            lambda v: v in (3, 4),
        ),
        (
            "整个假期",
            {"destination": "北京", "departure_city": "上海", "departure_date": "2026-06-19"},
            "travel_days",
            3,
        ),
        (
            "整个小长假",
            {"destination": "北京", "departure_city": "上海", "departure_date": "2026-06-19"},
            "travel_days",
            3,
        ),
        (
            "假期都玩",
            {"destination": "北京", "departure_city": "上海", "departure_date": "2026-06-19"},
            "travel_days",
            3,
        ),
        (
            "放几天玩几天",
            {"destination": "成都", "departure_city": "上海", "departure_date": "2026-05-01"},
            "travel_days",
            5,
        ),
        (
            "就我一个人",
            {"destination": "成都", "departure_city": "上海", "departure_date": "2026-06-19", "travel_days": 3},
            "adult_count",
            1,
        ),
        (
            "2大1小",
            {"destination": "成都", "departure_city": "上海", "departure_date": "2026-06-19", "travel_days": 3},
            "children_count",
            1,
        ),
        (
            "一家三口",
            {"destination": "成都", "departure_city": "上海", "departure_date": "2026-06-19", "travel_days": 3},
            "children_count",
            1,
        ),
        (
            "老两口",
            {"destination": "成都", "departure_city": "上海", "departure_date": "2026-06-19", "travel_days": 3},
            "adult_count",
            2,
        ),
        (
            "穷游党",
            {
                "destination": "成都",
                "departure_city": "上海",
                "departure_date": "2026-06-19",
                "travel_days": 3,
                "adult_count": 2,
                "party_confirmed": True,
            },
            "budget_min",
            800,
        ),
        (
            "学生党",
            {
                "destination": "成都",
                "departure_city": "上海",
                "departure_date": "2026-06-19",
                "travel_days": 3,
                "adult_count": 2,
                "party_confirmed": True,
            },
            "budget_min",
            800,
        ),
        (
            "一般党",
            {
                "destination": "成都",
                "departure_city": "上海",
                "departure_date": "2026-06-19",
                "travel_days": 3,
                "adult_count": 2,
                "party_confirmed": True,
            },
            "budget_min",
            2000,
        ),
        (
            "富有党",
            {
                "destination": "成都",
                "departure_city": "上海",
                "departure_date": "2026-06-19",
                "travel_days": 3,
                "adult_count": 2,
                "party_confirmed": True,
            },
            "budget_min",
            5000,
        ),
        (
            "坐高铁",
            {"destination": "成都"},
            "special_needs",
            "高铁",
        ),
        (
            "飞过去",
            {"destination": "成都"},
            "special_needs",
            "飞机",
        ),
        (
            "5000",
            {
                "destination": "成都",
                "departure_city": "上海",
                "departure_date": "2026-06-19",
                "travel_days": 3,
                "adult_count": 2,
                "party_confirmed": True,
            },
            "pending_budget",
            True,
        ),
    ],
)
def test_oral_slot_binding(utterance, fields, check_key, expected):
    frame = bind_utterance_to_slots(utterance, fields, {})
    if check_key == "pending":
        assert frame.pending_clarification is not None
        assert frame.pending_clarification.get("candidate") == expected
    elif check_key == "pending_fuzzy":
        assert frame.pending_clarification is not None
        assert "destination" not in frame.slot_updates
        candidates = tuple(frame.pending_clarification.get("candidates") or ())
        for city in expected:
            assert city in candidates, f"missing {city} in {candidates}"
    elif check_key == "pending_budget":
        assert frame.pending_clarification is not None
        assert frame.pending_clarification.get("kind") == "budget_scope"
    elif check_key == "departure_date" and expected == "date":
        assert frame.slot_updates.get("departure_date") is not None
    elif check_key == "special_needs":
        value = frame.slot_updates.get(check_key)
        assert value and str(expected) in value, f"{utterance!r} -> {value}"
    else:
        value = frame.slot_updates.get(check_key)
        assert _check(expected, value), f"{utterance!r} -> {check_key}={value}, want {expected}"


# 口语扩展回归（normalizer / intent）
_COLLOQUIAL_CASES = [
    ("下礼拜五走", "下周"),
    ("一家三口", "2成人1儿童"),
    ("学生党", "穷游党"),
    ("坐高铁", "高铁出行"),
    ("我明天想粗去玩", "出去"),
    ("过两天", "后天"),
    ("带俩娃", "儿童"),
    ("随便玩玩", "一般党"),
    ("三四个天", "3-4天"),
    ("这礼拜", "本周"),
    ("飞过去", "飞机出行"),
    ("开车去", "自驾出行"),
    ("老两口", "2位成人"),
    ("2大1小", "2大1小"),
    ("下礼拜", "下周"),
    ("咋样", "怎么样"),
    ("啥时候", "什么时候"),
]


@pytest.mark.parametrize(("raw", "needle"), _COLLOQUIAL_CASES)
def test_colloquial_expansion(raw, needle):
    expanded = expand_colloquial_phrases(raw)
    normalized, _ = normalize_text(raw)
    assert needle in expanded or needle in normalized


# 目的地 resolver 批量
_CITY_TYPO_CASES = [
    ("程度", "成都"),
    ("成度", "成都"),
    ("杭洲", "杭州"),
    ("上诲", "上海"),
    ("广洲", "广州"),
    ("下门", "厦门"),
    ("夏门", "厦门"),
    ("青导", "青岛"),
    ("苏洲", "苏州"),
    ("郑洲", "郑州"),
    ("南京", "南京"),
    ("成都", "成都"),
    ("杭州", "杭州"),
    ("三亚", "三亚"),
    ("丽江", "丽江"),
    ("桂林", "桂林"),
    ("哈尔滨", "哈尔滨"),
    ("大连", "大连"),
    ("威海", "威海"),
    ("珠海", "珠海"),
]


@pytest.mark.parametrize(("typo", "city"), _CITY_TYPO_CASES)
def test_city_typo_resolution(typo, city):
    frame = bind_utterance_to_slots(typo, {}, {})
    resolved = frame.slot_updates.get("destination") or (
        frame.pending_clarification.get("candidate") if frame.pending_clarification else None
    )
    assert resolved == city
