"""目的地语义接入测试（P0.3）"""

from langchain_core.messages import AIMessage, HumanMessage

from app.graph.semantic.destination_semantics import apply_destination_semantics
from app.graph.templates.collect_followup import (
    render_destination_clarification,
    render_destination_unrecognized,
)


def test_clarify_chengdu_typo():
    messages = [
        AIMessage(content="你想去哪里玩？"),
        HumanMessage(content="程度"),
    ]
    fields, reply, pending = apply_destination_semantics({}, messages, {})
    assert reply == render_destination_clarification("成都", "程度")
    assert pending == {
        "slot": "destination",
        "kind": "city",
        "candidate": "成都",
        "original": "程度",
        "candidates": ["成都"],
    }
    assert "destination" not in fields


def test_confirm_typo_sets_destination():
    messages = [
        AIMessage(content="你是说「成都」吗？"),
        HumanMessage(content="对"),
    ]
    state = {
        "pending_clarification": {
            "slot": "destination",
            "candidate": "成都",
            "original": "程度",
        },
    }
    fields, reply, pending = apply_destination_semantics({}, messages, state)
    assert fields.get("destination") == "成都"
    assert pending == {}
    assert "出发" in (reply or "")


def test_exact_chengdu_accept():
    messages = [HumanMessage(content="成都")]
    fields, reply, pending = apply_destination_semantics({}, messages, {})
    assert fields.get("destination") == "成都"
    assert reply is None
    assert pending is None


def test_unrecognized_short_input():
    messages = [HumanMessage(content="哈哈")]
    fields, reply, pending = apply_destination_semantics({}, messages, {})
    assert reply == render_destination_unrecognized("哈哈")
    assert pending is None
