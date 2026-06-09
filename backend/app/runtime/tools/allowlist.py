"""V1 Runtime tool allowlist."""

from __future__ import annotations

V1_TOOL_ALLOWLIST: frozenset[str] = frozenset(
    {
        "weather.get_forecast",
        "date.resolve_relative_date",
        "holiday.resolve_holiday_hint",
    },
)

V1_RUNTIME_INVOCABLE_TOOLS: frozenset[str] = frozenset({"weather.get_forecast"})


def is_allowlisted(tool_name: str) -> bool:
    return tool_name in V1_TOOL_ALLOWLIST


def is_runtime_invocable(tool_name: str) -> bool:
    return tool_name in V1_RUNTIME_INVOCABLE_TOOLS


def assert_allowlisted(tool_name: str) -> None:
    if not is_allowlisted(tool_name):
        raise ValueError(f"Tool not allowlisted for Runtime V1: {tool_name}")
