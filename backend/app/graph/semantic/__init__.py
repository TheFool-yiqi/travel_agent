"""语义理解层（规范化、实体解析、歧义澄清）。"""

from app.graph.semantic.city_lexicon import CityMatch, lookup_city, match_cities
from app.graph.semantic.correction_handler import SlotCorrection, detect_user_correction
from app.graph.semantic.destination_resolver import DestinationResolution, resolve_destination_input
from app.graph.semantic.destination_semantics import apply_destination_semantics
from app.graph.semantic.disambiguator import Ambiguity, detect_ambiguities
from app.graph.semantic.frame import SemanticFrame, TextCorrection
from app.graph.semantic.intent_normalizer import expand_colloquial_phrases, extract_intent_slots
from app.graph.semantic.normalizer import normalize_text
from app.graph.semantic.place_lexicon import find_place_in_text, lookup_place, resolve_place_destination
from app.graph.semantic.semantic_metrics import (
    aggregate_session_metrics,
    build_turn_metrics,
    extract_traces_from_messages,
)
from app.graph.semantic.semantic_pipeline import (
    apply_semantic_frame,
    build_semantic_frame,
    semantic_frame_to_extraction,
    semantic_rule_extract_from_messages,
)
from app.graph.semantic.slot_tracker import bind_utterance_to_slots, compute_missing_slots

__all__ = [
    "Ambiguity",
    "CityMatch",
    "DestinationResolution",
    "SemanticFrame",
    "SlotCorrection",
    "TextCorrection",
    "aggregate_session_metrics",
    "apply_destination_semantics",
    "apply_semantic_frame",
    "bind_utterance_to_slots",
    "build_semantic_frame",
    "build_turn_metrics",
    "compute_missing_slots",
    "detect_ambiguities",
    "detect_user_correction",
    "expand_colloquial_phrases",
    "extract_intent_slots",
    "extract_traces_from_messages",
    "find_place_in_text",
    "lookup_city",
    "lookup_place",
    "match_cities",
    "normalize_text",
    "resolve_destination_input",
    "resolve_place_destination",
    "semantic_frame_to_extraction",
    "semantic_rule_extract_from_messages",
]
