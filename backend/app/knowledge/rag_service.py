"""RAG 管道单例与检索服务（供 rag_query、Agent 工具共用）。"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from langchain_core.documents import Document
from loguru import logger

from app.knowledge.document_loader import DocumentManager
from app.knowledge.document_splitter import AdvancedParentDocumentSplitter
from app.knowledge.query_optimizer import QueryStrategyInput
from app.knowledge.rag_pipeline import AdvancedRAGPipeline
from app.knowledge.vector_store import VectorStoreManager

if TYPE_CHECKING:
    from langchain_chroma import Chroma

_pipeline: AdvancedRAGPipeline | None = None
_init_lock = asyncio.Lock()


def load_vectorstore_bundle() -> tuple[Chroma, list[Document]]:
    """从持久化向量库加载 Chroma 与子文档列表。"""
    manager = VectorStoreManager()
    vectorstore = manager.get_vectorstore()
    payload = vectorstore._collection.get(include=["documents", "metadatas"])
    documents = payload.get("documents") or []
    metadatas = payload.get("metadatas") or []
    child_docs = [
        Document(page_content=text, metadata=meta or {})
        for text, meta in zip(documents, metadatas, strict=False)
        if text
    ]
    return vectorstore, child_docs


def _bootstrap_vectorstore_from_documents() -> tuple[Chroma, list[Document]]:
    """向量库不可用时，从 Markdown 文档切分并创建（与 init_rag 类似）。"""
    doc_manager = DocumentManager()
    documents = doc_manager.load_all_documents()
    if not documents:
        raise RuntimeError("未找到 RAG 文档，请先运行 scripts/init_rag.py")

    splitter = AdvancedParentDocumentSplitter()
    parent_docs, child_docs = splitter.split_documents(documents)
    if not child_docs:
        raise RuntimeError("文档切分后无子文档")

    vs_manager = VectorStoreManager()
    vectorstore = vs_manager.create_vectorstore(child_docs)

    parent_store = vs_manager.persist_directory / "parent_docs.jsonl"
    if not parent_store.is_file():
        import json

        with parent_store.open("w", encoding="utf-8") as file:
            for doc in parent_docs:
                record = {
                    "parent_id": doc.metadata.get("parent_id"),
                    "page_content": doc.page_content,
                    "metadata": doc.metadata,
                }
                file.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info("已从文档重建向量库: {} 个子文档", len(child_docs))
    return vectorstore, child_docs


def get_rag_pipeline(
    *,
    query_strategy: QueryStrategyInput = "multi_query",
    use_llm_reranker: bool = False,
    top_k: int = 3,
    enable_cache: bool = True,
    force_reload: bool = False,
) -> AdvancedRAGPipeline:
    """获取全局 AdvancedRAGPipeline 单例。"""
    global _pipeline

    if _pipeline is not None and not force_reload:
        return _pipeline

    logger.info("初始化 RAG 管道...")

    try:
        vectorstore, child_docs = load_vectorstore_bundle()
        logger.info("向量库加载成功，子文档 {} 个", len(child_docs))
    except Exception as exc:
        logger.warning("向量库加载失败，尝试从文档重建: {}", exc)
        vectorstore, child_docs = _bootstrap_vectorstore_from_documents()

    if not child_docs:
        raise RuntimeError("向量库为空，请先运行 scripts/init_rag.py")

    parent_splitter = AdvancedParentDocumentSplitter()
    _pipeline = AdvancedRAGPipeline(
        vectorstore=vectorstore,
        all_documents=child_docs,
        parent_splitter=parent_splitter,
        query_strategy=query_strategy,
        use_llm_reranker=use_llm_reranker,
        top_k=top_k,
        enable_cache=enable_cache,
    )
    logger.info("RAG 管道初始化完成")
    return _pipeline


async def get_rag_pipeline_async(
    *,
    query_strategy: QueryStrategyInput = "multi_query",
    use_llm_reranker: bool = False,
    top_k: int = 3,
    enable_cache: bool = True,
) -> AdvancedRAGPipeline:
    """异步安全地获取 RAG 管道单例。"""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    async with _init_lock:
        if _pipeline is None:
            return await asyncio.to_thread(
                get_rag_pipeline,
                query_strategy=query_strategy,
                use_llm_reranker=use_llm_reranker,
                top_k=top_k,
                enable_cache=enable_cache,
            )
    return _pipeline


def retrieve_documents(query: str) -> list[Document]:
    """通过管道检索文档。"""
    pipeline = get_rag_pipeline()
    return pipeline.retrieve(query)


def search_knowledge(query: str, *, enhanced_query: str | None = None) -> str:
    """同步 RAG 检索并格式化（供协调器 sync invoke 使用）。"""
    search_query = enhanced_query or query
    documents = retrieve_documents(search_query)
    return format_rag_results(documents, query)


def format_rag_results(documents: list[Document], query: str, *, max_chars: int = 800) -> str:
    """格式化 RAG 检索结果为 Agent 可读文本。"""
    if not documents:
        return f"未找到与「{query}」相关的信息。"

    parts: list[str] = []
    for i, doc in enumerate(documents, 1):
        content = doc.page_content
        if len(content) > max_chars:
            content = content[:max_chars] + "..."

        source = doc.metadata.get("source", "未知来源")
        city = doc.metadata.get("city")
        header = f"【资料 {i}】"
        if city:
            header += f"（{city}）"
        parts.append(f"{header}\n{content}\n来源：{source}")

    return "\n\n".join(parts)
