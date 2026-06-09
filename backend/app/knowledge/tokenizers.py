"""Chinese tokenization boundary for EvidenceEngine BM25 retrieval."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ChineseTokenizer(Protocol):
    def tokenize(self, text: str) -> list[str]:
        """Return whitespace-delimited tokens for BM25 indexing/search."""


class JiebaTokenizer:
    """V1 adapter isolating jieba usage from retrieval code paths."""

    def tokenize(self, text: str) -> list[str]:
        import jieba

        return [token.strip() for token in jieba.cut(text) if token.strip()]
