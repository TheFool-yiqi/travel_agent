"""Early greeting prefetch in chat stream."""

from app.graph.greeting import build_greeting_reply, is_greeting_only_text


def test_greeting_only_text() -> None:
    assert is_greeting_only_text("你好！") is True
    assert is_greeting_only_text("Hello") is True
    assert is_greeting_only_text("上海") is False


def test_greeting_reply_is_non_empty() -> None:
    reply = build_greeting_reply()
    assert "出发" not in reply
    assert "去哪" in reply or "去哪里" in reply


def test_greeting_reply_focuses_on_destination() -> None:
    reply = build_greeting_reply()
    assert "端午" not in reply
    assert "中秋" not in reply
