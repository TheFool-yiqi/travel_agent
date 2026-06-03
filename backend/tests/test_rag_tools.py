"""RAG Agent 工具（无 LLM）。"""

from __future__ import annotations

from langchain_core.documents import Document

from app.knowledge.rag_service import format_rag_results
from app.tools.rag import get_rag_tools


def test_format_rag_results_empty() -> None:
    assert "未找到" in format_rag_results([], "西安景点")


def test_format_rag_results_with_docs() -> None:
    docs = [
        Document(
            page_content="兵马俑介绍",
            metadata={"source": "xian.md", "city": "西安"},
        )
    ]
    text = format_rag_results(docs, "西安景点")
    assert "兵马俑" in text
    assert "西安" in text
    assert "xian.md" in text


def test_get_rag_tools_count() -> None:
    assert len(get_rag_tools()) == 4
