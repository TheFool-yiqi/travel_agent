"""Step router tests."""

from app.graph.routers.step_router import route_after_collect


def test_route_after_collect_requires_user_confirmed() -> None:
    state = {
        "requirements_complete": True,
        "user_requirement": {"departure_city": "上海"},
        "user_confirmed": False,
    }
    assert route_after_collect(state) == "__end__"


def test_route_after_collect_advances_when_confirmed() -> None:
    state = {
        "requirements_complete": True,
        "user_requirement": {"departure_city": "上海"},
        "user_confirmed": True,
    }
    assert route_after_collect(state) == "plan_destination"
