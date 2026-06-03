"""RAG 知识层：父文档 + 子文档切分策略。"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger


class ParentDocumentSplitter:
    """
    父文档切分器。

    策略：
    - 父文档：较大块（默认 1000 字符），用于最终上下文
    - 子文档：较小块（默认 200 字符），用于向量检索
    - 子文档通过 metadata["parent_id"] 关联父文档
    """

    _SEPARATORS = ["\n\n", "\n", "。", "，", " ", ""]

    def __init__(
        self,
        parent_chunk_size: int = 1000,
        parent_chunk_overlap: int = 200,
        child_chunk_size: int = 200,
        child_chunk_overlap: int = 50,
    ) -> None:
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_chunk_size,
            chunk_overlap=parent_chunk_overlap,
            separators=self._SEPARATORS,
        )
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_chunk_size,
            chunk_overlap=child_chunk_overlap,
            separators=self._SEPARATORS,
        )

    def split_documents(
        self,
        documents: list[Document],
    ) -> tuple[list[Document], list[Document]]:
        """
        切分文档为父文档和子文档。

        Returns:
            parent_docs: 父文档列表（含 parent_id）
            child_docs: 子文档列表（含 parent_id，指向所属父块）
        """
        parent_docs: list[Document] = []
        child_docs: list[Document] = []

        for doc in documents:
            parent_chunks = self.parent_splitter.split_documents([doc])

            for i, parent_chunk in enumerate(parent_chunks):
                parent_id = f"{doc.metadata.get('source', 'unknown')}_{i}"
                parent_chunk.metadata = {
                    **parent_chunk.metadata,
                    "parent_id": parent_id,
                    "chunk_level": "parent",
                }
                parent_docs.append(parent_chunk)

                for child_chunk in self.child_splitter.split_documents([parent_chunk]):
                    child_chunk.metadata = {
                        **child_chunk.metadata,
                        "parent_id": parent_id,
                        "chunk_level": "child",
                    }
                    child_docs.append(child_chunk)

        logger.info(
            "切分完成: {} 个父文档, {} 个子文档",
            len(parent_docs),
            len(child_docs),
        )
        return parent_docs, child_docs


class AdvancedParentDocumentSplitter(ParentDocumentSplitter):
    """
    高级父文档切分器：切分 + 子文档 → 父文档上下文映射。

    初始化时可传入切分得到的 parent_docs，或留空并从 parent_docs.jsonl 加载索引。
    """

    def __init__(
        self,
        parent_docs: list[Document] | None = None,
        parent_index: dict[str, str] | None = None,
        parent_chunk_size: int = 1000,
        parent_chunk_overlap: int = 200,
        child_chunk_size: int = 200,
        child_chunk_overlap: int = 50,
    ) -> None:
        super().__init__(
            parent_chunk_size=parent_chunk_size,
            parent_chunk_overlap=parent_chunk_overlap,
            child_chunk_size=child_chunk_size,
            child_chunk_overlap=child_chunk_overlap,
        )
        if parent_index is not None:
            self._parent_index = parent_index
        elif parent_docs:
            self._parent_index = {
                str(doc.metadata["parent_id"]): doc.page_content
                for doc in parent_docs
                if doc.metadata.get("parent_id")
            }
        else:
            from app.knowledge.parent_store import load_parent_index

            self._parent_index = load_parent_index()

    def get_parent_context(self, child_docs: list[Document]) -> list[Document]:
        """按 parent_id 去重，回填父文档；缺失时保留子文档。"""
        from app.knowledge.hybrid_retriever import _doc_key

        parents: list[Document] = []
        seen: set[str] = set()

        for child in child_docs:
            parent_id = child.metadata.get("parent_id")
            if parent_id and str(parent_id) in self._parent_index:
                key = str(parent_id)
                if key in seen:
                    continue
                seen.add(key)
                parents.append(
                    Document(
                        page_content=self._parent_index[key],
                        metadata={
                            **child.metadata,
                            "parent_id": parent_id,
                            "chunk_level": "parent",
                        },
                    )
                )
            else:
                key = _doc_key(child)
                if key in seen:
                    continue
                seen.add(key)
                parents.append(child)

        return parents
