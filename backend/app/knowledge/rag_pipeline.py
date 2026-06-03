"""Advanced RAG 管道：查询优化 → 混合检索 → 重排序 → 父文档映射 → 长上下文重排。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.documents import Document
from loguru import logger

from app.knowledge.document_splitter import AdvancedParentDocumentSplitter
from app.knowledge.hybrid_retriever import AdvancedHybridRetriever
from app.knowledge.llm_reranker import LLMReranker, LongContextReorder
from app.knowledge.query_optimizer import AdvancedQueryOptimizer, QueryStrategyInput
from app.knowledge.rag_cache import RAGCache

if TYPE_CHECKING:
    from langchain_chroma import Chroma


class AdvancedRAGPipeline:
    """
    高级 RAG 管道。

    完整流程：
    查询优化 → 混合检索 → 重排序 → 父文档映射 → 长上下文重排序
    """

    def __init__(
        self,
        vectorstore: Chroma,
        all_documents: list[Document],
        parent_splitter: AdvancedParentDocumentSplitter,
        *,
        query_strategy: QueryStrategyInput = "auto",
        use_llm_reranker: bool = True,
        top_k: int = 3,
        enable_cache: bool = True,
        cache_ttl: int = 3600,
        cache: RAGCache | None = None,
    ) -> None:
        self.top_k = top_k
        self.use_llm_reranker = use_llm_reranker

        self.query_optimizer = AdvancedQueryOptimizer(strategy=query_strategy)
        self.retriever = AdvancedHybridRetriever(
            vectorstore=vectorstore,
            documents=all_documents,
            k=top_k * 3,
        )
        self.reranker = LLMReranker(top_k=top_k * 2)
        self.parent_splitter = parent_splitter
        self.context_reorder = LongContextReorder()
        self.cache = cache if cache is not None else RAGCache(ttl=cache_ttl, enabled=enable_cache)

    def retrieve(self, query: str) -> list[Document]:
        """
        完整检索流程。

        Args:
            query: 用户查询

        Returns:
            优化后的上下文文档列表（父文档优先）
        """
        cached_result = self.cache.get(query, self.top_k)
        if cached_result:
            return cached_result

        logger.info("开始 Advanced RAG 检索: {}", query)

        optimized_queries = self.query_optimizer.optimize(query)
        logger.info("1. 查询优化完成，生成 {} 个查询", len(optimized_queries))

        child_docs = self.retriever.retrieve(
            query=query,
            queries=optimized_queries,
        )
        logger.info("2. 混合检索完成，获得 {} 个候选文档", len(child_docs))

        if self.use_llm_reranker:
            reranked_child_docs = self.reranker.rerank(
                query=query,
                documents=child_docs,
                top_k=self.top_k * 2,
            )
        else:
            reranked_child_docs = child_docs[: self.top_k * 2]
        logger.info("3. 重排序完成，保留 {} 个文档", len(reranked_child_docs))

        parent_docs = self.parent_splitter.get_parent_context(reranked_child_docs)
        logger.info("4. 父文档映射完成，获得 {} 个完整上下文", len(parent_docs))

        final_docs = self.context_reorder.reorder(parent_docs[: self.top_k])
        logger.info("RAG 检索完成，最终返回 {} 个文档", len(final_docs))

        self.cache.set(query, self.top_k, final_docs)

        return final_docs
