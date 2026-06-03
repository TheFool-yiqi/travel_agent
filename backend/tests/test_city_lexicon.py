"""城市词表与模糊匹配测试（P0.1）"""

from app.graph.semantic.city_lexicon import lookup_city, match_cities


def test_lookup_exact_city():
    assert lookup_city("成都") is not None
    assert lookup_city("成都").name == "成都"


def test_lookup_alias():
    assert lookup_city("版纳") is not None
    assert lookup_city("版纳").name == "西双版纳"


def test_lookup_rongcheng_alias():
    entry = lookup_city("蓉城")
    assert entry is not None
    assert entry.name == "成都"


def test_match_typo_confirm_chengdu():
    matches = match_cities("程度")
    assert matches
    assert matches[0].city == "成都"
    assert matches[0].needs_confirm is True


def test_match_exact_chengdu():
    matches = match_cities("成都")
    assert matches[0].city == "成都"
    assert matches[0].confidence == 1.0
    assert matches[0].needs_confirm is False


def test_match_visual_typo_hangzhou():
    matches = match_cities("杭洲")
    assert matches
    assert matches[0].city == "杭州"
    assert matches[0].needs_confirm is False


def test_match_empty():
    assert match_cities("") == []
    assert match_cities("   ") == []
