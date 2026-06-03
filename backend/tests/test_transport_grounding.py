"""Transport reply grounding tests."""

from app.graph.validators.transport import validate_transport_reply


def test_validate_transport_reply_flags_unknown_flight() -> None:
    tool_context = "可选高铁 G1234 上海虹桥-成都东"
    reply = "推荐航班 MU5101 和高铁 G1234"
    errors = validate_transport_reply(reply, tool_context)
    assert any("MU5101" in e for e in errors)
    assert not any("G1234" in e for e in errors)


def test_validate_transport_reply_skips_when_no_context() -> None:
    assert validate_transport_reply("航班 MU5101", "") == []
