"""place_lexicon 测试（P3.1）"""

from app.graph.semantic.place_lexicon import find_place_in_text, lookup_place, resolve_place_destination


def test_lookup_jiuzhai():
    assert lookup_place("九寨") == "九寨沟"


def test_lookup_banna():
    assert lookup_place("版纳") == "西双版纳"


def test_erhai_maps_dali():
    assert lookup_place("洱海") == "大理"


def test_find_in_sentence():
    found = find_place_in_text("想去洱海玩两天")
    assert found is not None
    assert found[1] == "大理"


def test_gulangyu():
    assert resolve_place_destination("鼓浪屿") == "厦门"


def test_huashan():
    assert lookup_place("华山") == "西安"


def test_niaochao_beijing():
    assert lookup_place("鸟巢") == "北京"
