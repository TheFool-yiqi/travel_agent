"""区域词表与 西藏/西安 类误匹配回归测试。"""

import pytest

from app.graph.semantic.destination_resolver import resolve_destination_input
from app.graph.semantic.region_lexicon import lookup_region
from app.graph.validators.requirements import sanitize_destination


def test_region_xizang_exact_accept():
    assert lookup_region("西藏") == "西藏"
    result = resolve_destination_input("西藏")
    assert result.action == "accept"
    assert result.city == "西藏"
    assert result.confidence == 1.0


def test_xizang_not_fuzzy_to_xian():
    """西藏与西安编辑距离为 1，不得自动采纳西安。"""
    result = resolve_destination_input("西藏")
    assert result.city != "西安"
    assert result.action == "accept"


def test_xian_exact_accept():
    result = resolve_destination_input("西安")
    assert result.action == "accept"
    assert result.city == "西安"


def test_typo_chengdu_still_clarify():
    result = resolve_destination_input("程度")
    assert result.action == "clarify"
    assert result.city == "成都"


def test_sanitize_strips_llm_xian_when_user_said_xizang():
    fields = {"destination": "西安"}
    dialogue = "用户: 西藏\n助手: 好的"
    cleaned = sanitize_destination(
        fields,
        dialogue_text=dialogue,
        guidance_step="destination",
    )
    assert "destination" not in cleaned


@pytest.mark.parametrize("typo,expected", [("杭洲", "杭州")])
def test_whitelist_typo_auto_still_accept(typo: str, expected: str):
    result = resolve_destination_input(typo)
    assert result.action == "accept"
    assert result.city == expected


def test_tiantang_fuzzy_clarify_not_auto_tianjin():
    """「天堂」与天津/天水均编辑距离 1，不得自动写入 destination。"""
    result = resolve_destination_input("天堂")
    assert result.action == "clarify"
    assert result.city in ("天津", "天水")
    assert "天津" in result.candidates


def test_tiantang_slot_binding_no_destination_until_confirm():
    from app.graph.semantic.slot_tracker import bind_utterance_to_slots

    frame = bind_utterance_to_slots("天堂", {}, {})
    assert "destination" not in frame.slot_updates
    assert frame.pending_clarification is not None
    assert frame.pending_clarification.get("slot") == "destination"


def test_sanitize_strips_llm_tianjin_when_user_said_tiantang():
    fields = {"destination": "天津"}
    dialogue = "用户: 天堂\n助手: 好的"
    cleaned = sanitize_destination(
        fields,
        dialogue_text=dialogue,
        guidance_step="destination",
    )
    assert "destination" not in cleaned


def test_sanitize_keeps_destination_when_user_answers_departure_city():
    """已确认成都后用户答上海，不应误删 destination。"""
    fields = {"destination": "成都", "departure_city": "上海"}
    dialogue = "用户: 成都\n助手: 好的\n用户: 上海"
    cleaned = sanitize_destination(
        fields,
        dialogue_text=dialogue,
        guidance_step="departure_city",
    )
    assert cleaned.get("destination") == "成都"
    assert cleaned.get("departure_city") == "上海"


def test_tianshui_exact_accept():
    result = resolve_destination_input("天水")
    assert result.action == "accept"
    assert result.city == "天水"


def test_tianjin_exact_accept():
    result = resolve_destination_input("天津")
    assert result.action == "accept"
    assert result.city == "天津"
    assert result.city != "天水"


def test_didu_alias_beijing():
    result = resolve_destination_input("帝都")
    assert result.action == "accept"
    assert result.city == "北京"


def test_modu_alias_shanghai():
    result = resolve_destination_input("魔都")
    assert result.action == "accept"
    assert result.city == "上海"


def test_beijing_pinyin_case_insensitive():
    result = resolve_destination_input("Beijing")
    assert result.action == "accept"
    assert result.city == "北京"


def test_pinyin_abbrev_bj_cd():
    assert resolve_destination_input("bj").city == "北京"
    assert resolve_destination_input("cd").city == "成都"


def test_yunnan_region_accept():
    result = resolve_destination_input("云南")
    assert result.action == "accept"
    assert result.city == "云南"


def test_chuanxi_region_alias():
    assert lookup_region("川西") == "四川"
    result = resolve_destination_input("川西")
    assert result.action == "accept"
    assert result.city == "四川"


def test_sanitize_casual_input_strips_destination():
    fields = {"destination": "随便"}
    dialogue = "用户: 随便\n助手: 好的"
    cleaned = sanitize_destination(fields, dialogue_text=dialogue, guidance_step="destination")
    assert "destination" not in cleaned


def test_rongcheng_alias_chengdu():
    result = resolve_destination_input("蓉城")
    assert result.action == "accept"
    assert result.city == "成都"


def test_niaochao_place_beijing():
    from app.graph.semantic.place_lexicon import lookup_place

    assert lookup_place("鸟巢") == "北京"
