"""规划选择 NL 规则抽取。"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from app.graph.nl_extract import _rule_based_selection, resolve_confirmed_destination


def test_rule_based_comfort_and_cost_aliases() -> None:
    cheap = _rule_based_selection("便宜点，坐高铁", assistant_text="请选择交通")
    assert cheap.selected_transport == "train"
    assert "economy_hotel" in cheap.selected_accommodation_types

    comfy = _rule_based_selection("舒服点，飞机吧", assistant_text="请选择交通")
    assert comfy.selected_transport == "flight"
    assert "star_hotel" in comfy.selected_accommodation_types


def test_rule_based_ignores_assistant_transport_options() -> None:
    extracted = _rule_based_selection(
        "都行，你看着办",
        assistant_text="可选 flight / train / driving，请问偏好？",
    )
    assert extracted.selected_transport is None


def test_rule_based_ordinal_destination_from_assistant_list() -> None:
    extracted = _rule_based_selection(
        "就第二个吧",
        assistant_text="推荐三个目的地：1. 杭州 2. 苏州 3. 南京",
    )
    assert extracted.selected_destination == "苏州"


def test_resolve_confirmed_destination_rejects_collect_intent_only() -> None:
    messages = [HumanMessage(content="我想去成都")]
    assert (
        resolve_confirmed_destination(
            messages,
            selected_destination=None,
            extracted_destination="成都",
        )
        is None
    )


def test_resolve_confirmed_destination_accepts_explicit_city() -> None:
    messages = [
        AIMessage(content="推荐三个目的地：1. 杭州 2. 苏州 3. 南京"),
        HumanMessage(content="去成都吧"),
    ]
    assert (
        resolve_confirmed_destination(
            messages,
            selected_destination=None,
            extracted_destination="成都",
        )
        == "成都"
    )


def test_resolve_confirmed_destination_accepts_ordinal_from_assistant_list() -> None:
    messages = [
        AIMessage(content="推荐三个目的地：1. 杭州 2. 苏州 3. 南京"),
        HumanMessage(content="第二个"),
    ]
    assert (
        resolve_confirmed_destination(
            messages,
            selected_destination=None,
            extracted_destination="苏州",
        )
        == "苏州"
    )


def test_resolve_confirmed_destination_rejects_vague_confirm_without_candidate() -> None:
    messages = [
        AIMessage(content="推荐三个目的地：1. 杭州 2. 苏州 3. 南京"),
        HumanMessage(content="可以"),
    ]
    assert (
        resolve_confirmed_destination(
            messages,
            selected_destination=None,
            extracted_destination="杭州",
        )
        is None
    )


def test_resolve_confirmed_destination_accepts_delegation_with_recommendations() -> None:
    messages = [
        AIMessage(content="为您推荐三个目的地：1. 杭州 2. 苏州 3. 南京"),
        HumanMessage(content="听你的"),
    ]
    assert (
        resolve_confirmed_destination(
            messages,
            selected_destination=None,
            extracted_destination=None,
        )
        == "杭州"
    )
