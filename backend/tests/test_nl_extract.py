"""nl_extract rule-based selection tests."""

from __future__ import annotations

from app.graph.nl_extract import _rule_based_selection


def test_rule_transport_flight() -> None:
    result = _rule_based_selection("我想坐飞机去")
    assert result.selected_transport == "flight"


def test_rule_transport_train() -> None:
    result = _rule_based_selection("坐高铁吧")
    assert result.selected_transport == "train"


def test_rule_accommodation_and_food() -> None:
    result = _rule_based_selection("住经济型酒店，吃本地小吃")
    assert "economy_hotel" in result.selected_accommodation_types
    assert "local" in result.selected_food_types


def test_rule_destination() -> None:
    result = _rule_based_selection("想去成都")
    assert result.selected_destination == "成都"
