"""Runtime semantic layer adapter tests."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.runtime.semantic.collection_frame import CollectSemanticLayer
from app.runtime.semantic.normalizer import normalize_text


def test_runtime_normalizer_wraps_graph_rules() -> None:
    normalized, corrections = normalize_text("粗去 玩几天")

    assert "出去" in normalized
    assert corrections


def test_collect_semantic_layer_runs_rule_extract_before_llm_fields() -> None:
    messages = [HumanMessage(content="成都")]
    trip_spec: dict = {}
    state: dict = {"pending_clarification": None}

    extraction, frame = CollectSemanticLayer.rule_extract(messages, trip_spec, state)

    assert extraction.destination == "成都" or frame.slot_updates.get("destination") == "成都"
    assert frame.extraction_source in {"rule", "fuzzy", "hybrid"}
