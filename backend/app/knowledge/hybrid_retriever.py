"""RAG 知识层：BM25 + Dense + RRF 混合检索（含 AdvancedHybridRetriever）。"""

from __future__ import annotations

from collections import defaultdict

from langchain_chroma import Chroma
from langchain_core.documents import Document
from loguru import logger
from rank_bm25 import BM25Okapi

import jieba


def _doc_key(doc: Document) -> str:
    """用于 RRF / 去重的稳定文档键。"""
    parent_id = doc.metadata.get("parent_id")
    if parent_id:
        return f"{parent_id}|{doc.page_content}"
    source = doc.metadata.get("source", "")
    return f"{source}|{doc.page_content}"


class HybridRetriever:
    """
    混合检索器。

    结合：
    - BM25（关键词匹配，jieba 分词）
    - Dense（Chroma 向量相似度）
    - RRF（Reciprocal Rank Fusion 倒数排名融合）
    """

    def __init__(
        self,
        vectorstore: Chroma,
        documents: list[Document],
        k: int = 5,
        candidate_multiplier: int = 2,
        rrf_k: int = 60,
    ) -> None:
        self.vectorstore = vectorstore
        self.documents = documents
        self.k = k
        self.candidate_multiplier = candidate_multiplier
        self.rrf_k = rrf_k
        self._init_bm25()

    def _init_bm25(self) -> None:
        logger.info("初始化 BM25 索引，文档数={}", len(self.documents))
        tokenized_docs = [list(jieba.cut(doc.page_content)) for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_docs)
        logger.info("BM25 索引初始化完成")

    def retrieve(self, query: str) -> list[Document]:
        """
        混合检索。

        1. BM25 取 top 候选
        2. Dense 取 top 候选
        3. RRF 融合后返回 top-k
        """
        candidate_k = self.k * self.candidate_multiplier

        query_tokens = list(jieba.cut(query))
        bm25_scores = self.bm25.get_scores(query_tokens)
        bm25_top_indices = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True,
        )[:candidate_k]
        bm25_docs = [(self.documents[i], float(bm25_scores[i])) for i in bm25_top_indices]

        logger.debug("BM25 检索到 {} 个候选", len(bm25_docs))

        dense_docs = self.vectorstore.similarity_search_with_score(query, k=candidate_k)
        logger.debug("Dense 检索到 {} 个候选", len(dense_docs))

        fused_docs = self._rrf_fusion(bm25_docs, dense_docs)
        logger.info("混合检索完成，返回 {} 个结果", len(fused_docs))
        return fused_docs

    def _rrf_fusion(
        self,
        bm25_docs: list[tuple[Document, float]],
        dense_docs: list[tuple[Document, float]],
    ) -> list[Document]:
        """
        倒数排名融合：score(d) = Σ 1 / (rrf_k + rank(d))
        """
        scores: dict[str, float] = {}
        all_docs: dict[str, Document] = {}

        for rank, (doc, _) in enumerate(bm25_docs, start=1):
            key = _doc_key(doc)
            all_docs[key] = doc
            scores[key] = scores.get(key, 0.0) + 1.0 / (self.rrf_k + rank)

        for rank, (doc, _) in enumerate(dense_docs, start=1):
            key = _doc_key(doc)
            all_docs[key] = doc
            scores[key] = scores.get(key, 0.0) + 1.0 / (self.rrf_k + rank)

        sorted_keys = sorted(scores, key=lambda key: scores[key], reverse=True)
        return [all_docs[key] for key in sorted_keys[: self.k]]


class AdvancedHybridRetriever:
    """
    高级混合检索器

    在 HybridRetriever 基础上支持：
    - 多 query 变体合并（配合 query_optimizer）
    - BM25 / Dense RRF 权重可配置
    - 结果缓存
    """

    def __init__(
        self,
        vectorstore: Chroma,
        documents: list[Document],
        k: int = 5,
        candidate_multiplier: int = 2,
        rrf_k: int = 60,
        bm25_weight: float = 0.4,
        dense_weight: float = 0.6,
        use_cache: bool = True,
    ) -> None:
        self.vectorstore = vectorstore
        self.documents = documents
        self.k = k
        self.candidate_multiplier = candidate_multiplier
        self.rrf_k = rrf_k
        self.bm25_weight = bm25_weight
        self.dense_weight = dense_weight
        self.use_cache = use_cache
        self._cache: dict[str, list[Document]] | None = {} if use_cache else None
        self._init_bm25()

    def _init_bm25(self) -> None:
        logger.info("初始化 AdvancedHybrid BM25 索引，文档数={}", len(self.documents))
        tokenized_docs = [list(jieba.cut(doc.page_content)) for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_docs)
        logger.info("AdvancedHybrid BM25 索引初始化完成")

    def clear_cache(self) -> None:
        """清空检索缓存。"""
        if self._cache is not None:
            self._cache.clear()

    def retrieve(
        self,
        query: str,
        queries: list[str] | None = None,
    ) -> list[Document]:
        """
        混合检索。

        Args:
            query: 主查询（用于缓存键）
            queries: 可选查询变体（Multi-Query / hybrid 策略输出）
        """
        query = query.strip()
        if not query:
            return []

        if self._cache is not None and query in self._cache:
            logger.info("混合检索命中缓存: {}", query[:40])
            return self._cache[query]

        variant_queries = queries or [query]
        if len(variant_queries) > 1:
            logger.info("使用 {} 个查询变体进行混合检索", len(variant_queries))
            merged: list[Document] = []
            seen: set[str] = set()
            for variant in variant_queries:
                for doc in self._single_retrieve(variant.strip()):
                    key = _doc_key(doc)
                    if key not in seen:
                        seen.add(key)
                        merged.append(doc)
            final_results = merged[: self.k]
        else:
            final_results = self._single_retrieve(query)

        if self._cache is not None:
            self._cache[query] = final_results

        return final_results

    def _single_retrieve(self, query: str) -> list[Document]:
        candidate_k = self.k * self.candidate_multiplier

        query_tokens = list(jieba.cut(query))
        bm25_scores = self.bm25.get_scores(query_tokens)
        bm25_top_indices = sorted(
            range(len(bm25_scores)),
            key=lambda index: bm25_scores[index],
            reverse=True,
        )[:candidate_k]
        bm25_results = [self.documents[index] for index in bm25_top_indices]

        dense_results = self.vectorstore.similarity_search_with_score(query, k=candidate_k)

        logger.debug("BM25 检索到 {} 个候选", len(bm25_results))
        logger.debug("Dense 检索到 {} 个候选", len(dense_results))

        fused = self._rrf_fusion(bm25_results, dense_results)
        logger.info("AdvancedHybrid 检索完成，返回 {} 个结果", len(fused))
        return fused

    def _rrf_fusion(
        self,
        bm25_results: list[Document],
        dense_results: list[tuple[Document, float]],
    ) -> list[Document]:
        """加权 RRF：score(d) = Σ weight / (rrf_k + rank)"""
        scores: dict[str, float] = defaultdict(float)
        doc_map: dict[str, Document] = {}

        for rank, doc in enumerate(bm25_results, start=1):
            key = _doc_key(doc)
            doc_map[key] = doc
            scores[key] += self.bm25_weight * (1.0 / (self.rrf_k + rank))

        for rank, (doc, _distance) in enumerate(dense_results, start=1):
            key = _doc_key(doc)
            doc_map[key] = doc
            scores[key] += self.dense_weight * (1.0 / (self.rrf_k + rank))

        sorted_keys = sorted(scores, key=lambda key: scores[key], reverse=True)
        return [doc_map[key] for key in sorted_keys[: self.k]]
