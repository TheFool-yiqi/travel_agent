"""文本规范化测试（P1.2）"""

from app.graph.semantic.normalizer import normalize_text


def test_normalize_trim():
    text, _corrections = normalize_text("  成都  ")
    assert text == "成都"


def test_normalize_colloquial_typo():
    text, corrections = normalize_text("我明天想粗去玩")
    assert "出去" in text
    assert any(c.reason == "typo" for c in corrections)


def test_normalize_fullwidth():
    text, _ = normalize_text("成都\u3000")
    assert text == "成都"
