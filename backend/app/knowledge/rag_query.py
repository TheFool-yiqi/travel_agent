"""RAG 检索编排：AdvancedRAGPipeline 入口与回退。"""

from __future__ import annotations

from langchain_core.documents import Document
from loguru import logger

from app.knowledge.document_splitter import AdvancedParentDocumentSplitter
from app.knowledge.guide_store import read_destination_guide
from app.knowledge.hybrid_retriever import HybridRetriever
from app.knowledge.llm_reranker import LLMReranker
from app.knowledge.query_optimizer import QueryStrategyInput
from app.knowledge.rag_pipeline import AdvancedRAGPipeline
from app.knowledge.rag_service import load_vectorstore_bundle


def _child_documents_from_vectorstore() -> tuple[object, list[Document]]:
    return load_vectorstore_bundle()


def rag_search(
    query: str,
    destination: str | None = None,
    *,
    top_k: int = 3,
    query_strategy: QueryStrategyInput | None = "auto",
    use_llm_reranker: bool = True,
    enable_cache: bool = True,
) -> str:
    """
    对知识库执行 Advanced RAG 检索，优先返回父文档上下文。
    向量库不可用时回退为整篇 Markdown 直读。

    Args:
        query_strategy:
            - None: 不做查询优化（单 query + HybridRetriever）
            - "auto": 按 query 特征自动选策略（推荐）
            - 或显式指定 multi_query / hyde / rewrite / hybrid / rewrite_hyde / full
    """
    search_query = f"{destination} {query}".strip() if destination else query

    try:
        vectorstore, child_docs = _child_documents_from_vectorstore()
    except Exception as exc:
        logger.warning("向量库不可用，回退整篇攻略: {}", exc)
        return _fallback_full_guide(destination, search_query)

    if not child_docs:
        return _fallback_full_guide(destination, search_query)

    if query_strategy is None:
        candidate_k = top_k * 2
        retriever = HybridRetriever(vectorstore, child_docs, k=candidate_k)
        candidates = retriever.retrieve(search_query)
        ranked = LLMReranker(top_k=top_k).rerank(
            search_query,
            candidates,
            top_k=top_k,
            long_context_reorder=True,
        )
    else:
        parent_splitter = AdvancedParentDocumentSplitter()
        pipeline = AdvancedRAGPipeline(
            vectorstore=vectorstore,
            all_documents=child_docs,
            parent_splitter=parent_splitter,
            query_strategy=query_strategy,
            use_llm_reranker=use_llm_reranker,
            top_k=top_k,
            enable_cache=enable_cache,
        )
        ranked = pipeline.retrieve(search_query)

    sections = [doc.page_content for doc in ranked]
    city = destination or (ranked[0].metadata.get("city", "目的地") if ranked else "目的地")
    body = "\n\n---\n\n".join(sections)
    return f"## {city} 知识库检索\n\n{body}"


def _fallback_full_guide(destination: str | None, query: str) -> str:
    if destination:
        guide = read_destination_guide(destination)
        if guide is not None:
            return guide
    return f"📍 未找到与「{query}」相关的本地攻略。"
