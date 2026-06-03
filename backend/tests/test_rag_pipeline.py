"""AdvancedRAGPipeline 与父文档映射（无 LLM）。"""

from __future__ import annotations

from langchain_core.documents import Document

from app.knowledge.document_splitter import AdvancedParentDocumentSplitter
from app.knowledge.llm_reranker import LongContextReorder


def test_parent_context_mapper_deduplicates_by_parent_id() -> None:
    index = {
        "guide_0": "父文档完整内容 A",
        "guide_1": "父文档完整内容 B",
    }
    children = [
        Document(page_content="子块1", metadata={"parent_id": "guide_0"}),
        Document(page_content="子块2", metadata={"parent_id": "guide_0"}),
        Document(page_content="子块3", metadata={"parent_id": "guide_1"}),
    ]
    splitter = AdvancedParentDocumentSplitter(parent_index=index)
    parents = splitter.get_parent_context(children)

    assert len(parents) == 2
    assert parents[0].page_content == "父文档完整内容 A"
    assert parents[1].page_content == "父文档完整内容 B"
    assert parents[0].metadata["chunk_level"] == "parent"


def test_parent_context_mapper_falls_back_to_child() -> None:
    child = Document(page_content="无父索引的子块", metadata={"source": "x"})
    splitter = AdvancedParentDocumentSplitter(parent_index={})
    parents = splitter.get_parent_context([child])

    assert len(parents) == 1
    assert parents[0].page_content == "无父索引的子块"


def test_long_context_reorder_interleaves() -> None:
    docs = [Document(page_content=str(i)) for i in range(5)]
    reordered = LongContextReorder.reorder(docs)
    assert [d.page_content for d in reordered] == ["0", "2", "4", "3", "1"]
