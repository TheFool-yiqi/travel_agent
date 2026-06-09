import pytest
from pydantic import ValidationError

from app.runtime.events import (
    RuntimeEvent,
    make_runtime_completed_event,
    make_runtime_failed_event,
    make_stage_completed_event,
    make_stage_started_event,
    runtime_event_to_transport,
)


def test_stage_started_event_transport_shape() -> None:
    event = make_stage_started_event(run_id="run_1", stage="collect")
    payload = runtime_event_to_transport(event)

    assert payload["type"] == "runtime_event"
    assert payload["event_type"] == "stage_started"
    assert payload["stage"] == "collect"
    assert payload["visibility"] == "public"
    assert payload["payload"] == {}


def test_stage_completed_event_contains_output_copy() -> None:
    output = {"status": "completed"}

    event = make_stage_completed_event(
        run_id="run_1",
        stage="collect",
        output=output,
    )
    output["status"] = "changed"

    assert event.payload == {"output": {"status": "completed"}}


def test_runtime_completed_event_has_no_stage() -> None:
    event = make_runtime_completed_event(run_id="run_1")

    assert event.type == "runtime_completed"
    assert event.stage is None
    assert event.visibility == "public"


def test_runtime_failed_event_supports_internal_visibility() -> None:
    event = make_runtime_failed_event(
        run_id="run_1",
        stage="collect",
        error={"message": "failed"},
        visibility="internal",
    )

    assert event.type == "runtime_failed"
    assert event.visibility == "internal"
    assert event.payload == {"error": {"message": "failed"}}


def test_stage_event_rejects_old_graph_name() -> None:
    with pytest.raises(ValueError, match="Unknown runtime stage"):
        make_stage_started_event(run_id="run_1", stage="build_itinerary")


def test_runtime_event_rejects_transport_only_type() -> None:
    with pytest.raises(ValidationError):
        RuntimeEvent(
            event_id="event_1",
            run_id="run_1",
            stage=None,
            type="done",
            visibility="public",
            payload={},
        )
