"""
手动测试 Advanced RAG 完整管道。

用法（在 backend 目录）：
    uv run python scripts/test_rag_pipeline.py
"""
from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.knowledge.document_loader import DocumentManager
from app.knowledge.document_splitter import AdvancedParentDocumentSplitter
from app.knowledge.rag_cache import RAGCache
from app.knowledge.rag_pipeline import AdvancedRAGPipeline
from app.knowledge.vector_store import VectorStoreManager
from app.utils.logging import setup_logger

setup_logger()


def _mock_redis_cache() -> RAGCache:
    store: dict[str, bytes] = {}
    client = MagicMock()
    client.ping.return_value = True
    client.get.side_effect = lambda key: store.get(key)
    client.setex.side_effect = lambda key, _ttl, value: store.update({key: value})
    return RAGCache(enabled=True, redis_client=client)


def main() -> None:
    print("\n=== 初始化 RAG 系统 ===")

    doc_manager = DocumentManager()
    documents = doc_manager.load_destination_documents()
    if not documents:
        print("未找到文档，请先添加 data/documents/destinations/")
        sys.exit(1)
    print(f"加载了 {len(documents)} 个文档")

    splitter = AdvancedParentDocumentSplitter()
    parent_docs, child_docs = splitter.split_documents(documents)
    splitter = AdvancedParentDocumentSplitter(parent_docs=parent_docs)
    print(f"父文档: {len(parent_docs)}, 子文档: {len(child_docs)}")

    vs_manager = VectorStoreManager(
        persist_directory=BACKEND_DIR.parent / "data" / "vectorstore" / "_pipeline_test",
        collection_name=f"manual_test_{uuid.uuid4().hex[:8]}",
    )
    vectorstore = vs_manager.create_vectorstore(child_docs)
    print("向量数据库创建成功")

    pipeline = AdvancedRAGPipeline(
        vectorstore=vectorstore,
        all_documents=child_docs,
        parent_splitter=splitter,
        query_strategy="multi_query",
        use_llm_reranker=False,
        top_k=1,
        cache=_mock_redis_cache(),
    )

    print("\n=== 测试检索 ===")
    test_queries = [
        "西安有哪些适合亲子游的景点？",
        "西安的美食推荐",
        "西安旅游的预算大概是多少？",
    ]

    first_elapsed = 0.0
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 测试 {i}: {query} ---")
        start = time.perf_counter()
        results = pipeline.retrieve(query)
        elapsed = time.perf_counter() - start
        if i == 1:
            first_elapsed = elapsed

        print(f"耗时: {elapsed:.2f}秒")
        print(f"返回了 {len(results)} 个文档")
        for j, doc in enumerate(results, 1):
            preview = doc.page_content[:120].replace("\n", " ")
            print(f"  [{j}] {preview}...")

    print("\n=== 缓存测试 ===")
    print("重复第一个查询...")
    start = time.perf_counter()
    cached_results = pipeline.retrieve(test_queries[0])
    cached_elapsed = time.perf_counter() - start

    print(f"缓存查询耗时: {cached_elapsed:.2f}秒")
    if cached_elapsed > 0:
        print(f"加速 {first_elapsed / cached_elapsed:.1f}x")
    assert cached_results


if __name__ == "__main__":
    main()
