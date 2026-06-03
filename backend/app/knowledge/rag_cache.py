"""RAG 检索结果 Redis 缓存。"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

import redis
from langchain_core.documents import Document
from loguru import logger

from app.settings import settings

if TYPE_CHECKING:
    from redis import Redis


class RAGCache:
    """
    RAG 检索结果缓存。

    使用 Redis 存储，key 为 query + top_k 的 MD5。
    连接失败时自动降级为无缓存。
    """

    def __init__(
        self,
        *,
        ttl: int = 3600,
        enabled: bool = True,
        redis_client: Redis | None = None,
    ) -> None:
        self.ttl = ttl
        self.enabled = enabled
        self.redis_client: Redis | None = redis_client

        if enabled and self.redis_client is None:
            try:
                password = settings.redis_password or None
                self.redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    password=password,
                    decode_responses=False,
                )
                self.redis_client.ping()
                logger.info("RAG Redis 缓存已启用")
            except Exception as exc:
                logger.warning("Redis 连接失败，禁用 RAG 缓存: {}", exc)
                self.enabled = False
                self.redis_client = None

    @staticmethod
    def _generate_key(query: str, top_k: int) -> str:
        content = f"{query}__k{top_k}"
        hash_value = hashlib.md5(content.encode()).hexdigest()
        return f"rag:cache:{hash_value}"

    @staticmethod
    def _serialize(documents: list[Document]) -> bytes:
        docs_data = [
            {"page_content": doc.page_content, "metadata": doc.metadata}
            for doc in documents
        ]
        return json.dumps(docs_data, ensure_ascii=False).encode("utf-8")

    @staticmethod
    def _deserialize(payload: bytes) -> list[Document]:
        docs_data = json.loads(payload)
        return [
            Document(page_content=item["page_content"], metadata=item["metadata"])
            for item in docs_data
        ]

    def get(self, query: str, top_k: int) -> list[Document] | None:
        """从缓存获取结果。"""
        if not self.enabled or self.redis_client is None:
            return None

        key = self._generate_key(query, top_k)
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                logger.info("RAG 缓存命中: {}...", query[:30])
                return self._deserialize(cached_data)
        except Exception as exc:
            logger.error("RAG 缓存读取失败: {}", exc)

        return None

    def set(self, query: str, top_k: int, documents: list[Document]) -> None:
        """缓存检索结果。"""
        if not self.enabled or self.redis_client is None:
            return

        key = self._generate_key(query, top_k)
        try:
            self.redis_client.setex(key, self.ttl, self._serialize(documents))
            logger.debug("RAG 结果已缓存: {}...", query[:30])
        except Exception as exc:
            logger.error("RAG 缓存写入失败: {}", exc)
