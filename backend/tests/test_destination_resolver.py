"""目的地解析测试（P0.2）"""

from app.graph.semantic.destination_resolver import resolve_destination_input


def test_chengdu_exact_accept():
    result = resolve_destination_input("成都")
    assert result.action == "accept"
    assert result.city == "成都"
    assert result.confidence >= 0.85


def test_chengdu_typo_clarify():
    result = resolve_destination_input("程度")
    assert result.action == "clarify"
    assert result.city == "成都"
    assert result.confidence >= 0.6


def test_hangzhou_typo_auto_accept():
    result = resolve_destination_input("杭洲")
    assert result.action == "accept"
    assert result.city == "杭州"


def test_unknown_none():
    result = resolve_destination_input("abcdef")
    assert result.action == "none"
