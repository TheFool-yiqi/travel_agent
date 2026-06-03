"""Advanced RAG 完整管道集成测试。"""

from __future__ import annotations

import time
import uuid
from unittest.mock import MagicMock

import pytest

from app.knowledge.document_loader import DocumentManager
from app.knowledge.document_splitter import AdvancedParentDocumentSplitter
from app.knowledge.rag_cache import RAGCache
from app.knowledge.rag_pipeline import AdvancedRAGPipeline
from app.knowledge.vector_store import VectorStoreManager
from app.settings import settings


def _mock_redis_cache() -> RAGCache:
    """内存 mock Redis，用于集成测试中的缓存断言。"""
    store: dict[str, bytes] = {}

    client = MagicMock()
    client.ping.return_value = True
    client.get.side_effect = lambda key: store.get(key)
    client.setex.side_effect = lambda key, _ttl, value: store.update({key: value})

    return RAGCache(enabled=True, redis_client=client)


@pytest.fixture
def rag_pipeline(tmp_path):
    """在临时目录构建完整 RAG 管道，不污染生产 vectorstore。"""
    doc_manager = DocumentManager()
    documents = doc_manager.load_destination_documents()
    if not documents:
        pytest.skip("未找到 destinations 文档，跳过集成测试")

    splitter = AdvancedParentDocumentSplitter()
    parent_docs, child_docs = splitter.split_documents(documents)
    splitter = AdvancedParentDocumentSplitter(parent_docs=parent_docs)

    vs_manager = VectorStoreManager(
        persist_directory=tmp_path / "vectorstore",
        collection_name=f"test_rag_{uuid.uuid4().hex[:8]}",
    )
    vectorstore = vs_manager.create_vectorstore(child_docs)

    pipeline = AdvancedRAGPipeline(
        vectorstore=vectorstore,
        all_documents=child_docs,
        parent_splitter=splitter,
        query_strategy="multi_query",
        use_llm_reranker=False,
        top_k=1,
        cache=_mock_redis_cache(),
    )
    return pipeline


@pytest.mark.integration
@pytest.mark.skipif(not settings.dashscope_api_key, reason="需要 DASHSCOPE_API_KEY（嵌入向量）")
@pytest.mark.skipif(not settings.mimo_api_key, reason="需要 MIMO_API_KEY（查询优化）")
def test_full_pipeline_retrieve(rag_pipeline: AdvancedRAGPipeline) -> None:
    """测试完整 RAG 管道：加载 → 切分 → 检索 → 返回父文档上下文。"""
    test_queries = [
        "西安有哪些适合亲子游的景点？",
        "西安的美食推荐",
        "西安旅游的预算大概是多少？",
    ]

    for query in test_queries:
        results = rag_pipeline.retrieve(query)

        assert len(results) == 1
        assert results[0].page_content.strip()
        assert len(results[0].page_content) > 50


@pytest.mark.integration
@pytest.mark.skipif(not settings.dashscope_api_key, reason="需要 DASHSCOPE_API_KEY（嵌入向量）")
@pytest.mark.skipif(not settings.mimo_api_key, reason="需要 MIMO_API_KEY（查询优化）")
def test_full_pipeline_cache_speedup(rag_pipeline: AdvancedRAGPipeline) -> None:
    """重复 query 应命中缓存并明显加速。"""
    query = "西安有哪些适合亲子游的景点？"

    first_elapsed = _timed_retrieve(rag_pipeline, query)
    second_elapsed = _timed_retrieve(rag_pipeline, query)

    assert second_elapsed < first_elapsed
    assert second_elapsed < 0.5


def _timed_retrieve(pipeline: AdvancedRAGPipeline, query: str) -> float:
    start = time.perf_counter()
    results = pipeline.retrieve(query)
    elapsed = time.perf_counter() - start
    assert results
    return elapsed
