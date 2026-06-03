"""RAGCache 序列化与 Redis 交互（mock）。"""

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_core.documents import Document

from app.knowledge.rag_cache import RAGCache


def test_generate_key_is_stable() -> None:
    key_a = RAGCache._generate_key("西安 景点", 3)
    key_b = RAGCache._generate_key("西安 景点", 3)
    key_c = RAGCache._generate_key("西安 景点", 5)

    assert key_a == key_b
    assert key_a != key_c
    assert key_a.startswith("rag:cache:")


def test_serialize_roundtrip() -> None:
    docs = [
        Document(page_content="段落 A", metadata={"parent_id": "p1", "city": "西安"}),
        Document(page_content="段落 B", metadata={"parent_id": "p2"}),
    ]
    restored = RAGCache._deserialize(RAGCache._serialize(docs))

    assert len(restored) == 2
    assert restored[0].page_content == "段落 A"
    assert restored[0].metadata["city"] == "西安"


def test_get_returns_cached_documents() -> None:
    docs = [Document(page_content="cached", metadata={"k": "v"})]
    payload = RAGCache._serialize(docs)

    redis_client = MagicMock()
    redis_client.get.return_value = payload

    cache = RAGCache(enabled=True, redis_client=redis_client)
    result = cache.get("西安美食", top_k=3)

    assert result is not None
    assert result[0].page_content == "cached"
    redis_client.get.assert_called_once()


def test_set_writes_with_ttl() -> None:
    redis_client = MagicMock()
    cache = RAGCache(enabled=True, ttl=1800, redis_client=redis_client)
    docs = [Document(page_content="new", metadata={})]

    cache.set("西安交通", top_k=2, documents=docs)

    redis_client.setex.assert_called_once()
    args = redis_client.setex.call_args[0]
    assert args[1] == 1800
    assert RAGCache._deserialize(args[2])[0].page_content == "new"


def test_disabled_cache_is_noop() -> None:
    cache = RAGCache(enabled=False)
    assert cache.get("q", 3) is None
    cache.set("q", 3, [Document(page_content="x", metadata={})])
