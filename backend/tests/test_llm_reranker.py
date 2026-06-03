"""LLM 重排与长上下文重排（无 LLM）。"""

from __future__ import annotations

from langchain_core.documents import Document

from app.knowledge.llm_reranker import LongContextReorder


def test_long_context_reorder_places_best_first_and_second_last() -> None:
    docs = [Document(page_content=str(i)) for i in range(6)]
    reordered = LongContextReorder.reorder(docs)
    assert [doc.page_content for doc in reordered] == ["0", "2", "4", "5", "3", "1"]


def test_long_context_reorder_skips_short_lists() -> None:
    docs = [Document(page_content="a"), Document(page_content="b")]
    assert LongContextReorder.reorder(docs) == docs
