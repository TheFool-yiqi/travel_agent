"""Text normalization adapter for collect semantic pre-pass."""

from __future__ import annotations

from app.graph.semantic.frame import TextCorrection
from app.graph.semantic.normalizer import normalize_text as _graph_normalize_text


def normalize_text(text: str) -> tuple[str, list[TextCorrection]]:
    """Normalize user input via the existing graph semantic normalizer."""
    return _graph_normalize_text(text)
