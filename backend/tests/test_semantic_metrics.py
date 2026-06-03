"""semantic_metrics 测试（P3.3）"""

from app.graph.semantic.frame import SemanticFrame, TextCorrection
from app.graph.semantic.semantic_metrics import aggregate_session_metrics, build_turn_metrics


def test_build_turn_metrics_first_hit():
    frame = SemanticFrame(
        normalized_text="成都",
        slot_updates={"destination": "成都"},
        guidance_step="destination",
        confidence=1.0,
    )
    metrics = build_turn_metrics(frame)
    assert metrics["first_hit"] is True
    assert metrics["slot_filled"] is True


def test_build_turn_metrics_clarification():
    frame = SemanticFrame(
        normalized_text="程度",
        pending_clarification={"slot": "destination", "candidate": "成都"},
        guidance_step="destination",
    )
    metrics = build_turn_metrics(frame)
    assert metrics["clarification_asked"] is True
    assert metrics["first_hit"] is False


def test_aggregate_session_metrics():
    traces = [
        {"metrics": {"first_hit": True, "slot_filled": True, "clarification_asked": False}},
        {"metrics": {"first_hit": False, "slot_filled": False, "clarification_asked": True}},
        {"metrics": {"first_hit": True, "slot_filled": True, "clarification_asked": False, "planning_reached": True}},
    ]
    agg = aggregate_session_metrics(traces)
    assert agg["turns"] == 3
    assert agg["first_hit_turns"] == 2
    assert agg["clarification_turns"] == 1
    assert agg["planning_reached"] is True
    assert agg["first_hit_rate"] == round(2 / 3, 4)
