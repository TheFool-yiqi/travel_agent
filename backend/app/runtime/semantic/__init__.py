"""Runtime-owned semantic pre-pass for collect."""

from app.runtime.semantic.collection_frame import CollectSemanticLayer
from app.runtime.semantic.normalizer import normalize_text

__all__ = ["CollectSemanticLayer", "normalize_text"]
