"""词表扩展回归测试。"""

import pytest

from app.graph.semantic.city_lexicon import lookup_city, match_cities
from app.graph.semantic.place_lexicon import lookup_place
from app.graph.semantic.region_lexicon import lookup_region
from app.graph.semantic.destination_resolver import resolve_destination_input


@pytest.mark.parametrize(
    ("name", "canonical"),
    [
        ("敦煌", "敦煌"),
        ("喀什", "喀什"),
        ("伊犁", "伊犁"),
        ("林芝", "林芝"),
        ("秦皇岛", "秦皇岛"),
        ("顺德", None),  # 未收录
    ],
)
def test_city_lookup_expanded(name: str, canonical: str | None):
    entry = lookup_city(name)
    if canonical is None:
        assert entry is None
    else:
        assert entry is not None
        assert entry.name == canonical


@pytest.mark.parametrize(
    ("alias", "city"),
    [
        ("赛里木湖", "伊犁"),
        ("喀纳斯", "阿勒泰"),
        ("洪崖洞", "重庆"),
        ("故宫", "北京"),
        ("那拉提", "伊犁"),
        ("冰雪大世界", "哈尔滨"),
    ],
)
def test_place_lookup_expanded(alias: str, city: str):
    assert lookup_place(alias) == city


@pytest.mark.parametrize(
    ("region", "canonical"),
    [
        ("南疆", "新疆"),
        ("北疆", "新疆"),
        ("藏区", "西藏"),
        ("川西", "四川"),
    ],
)
def test_region_alias_expanded(region: str, canonical: str):
    assert lookup_region(region) == canonical


def test_xizang_still_not_xian_after_city_expansion():
    result = resolve_destination_input("西藏")
    assert result.city == "西藏"
    matches = match_cities("西藏")
    # 模糊仍可能匹配西安，但 resolver 区域层优先
    assert result.action == "accept"
