"""RAG 知识层：Chroma 向量库管理。"""

from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from loguru import logger

from app.ai.embeddings import get_embedding_model
from app.settings import BASE_DIR


class VectorStoreManager:
    """向量数据库管理器（Chroma 持久化 + 千问嵌入）。"""

    def __init__(
        self,
        persist_directory: str | Path | None = None,
        collection_name: str = "travel_guides",
    ) -> None:
        self.persist_directory = Path(
            persist_directory or (Path(BASE_DIR) / "data" / "vectorstore")
        )
        self.collection_name = collection_name
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.embeddings = get_embedding_model()
        self.vectorstore: Chroma | None = None

    def create_vectorstore(self, documents: list[Document]) -> Chroma:
        """从文档创建并持久化向量库（会覆盖同名 collection 内容）。"""
        if not documents:
            raise ValueError("documents 不能为空")

        logger.info(
            "创建向量数据库 collection={} docs={} path={}",
            self.collection_name,
            len(documents),
            self.persist_directory,
        )

        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=str(self.persist_directory),
            collection_name=self.collection_name,
        )

        logger.info("向量数据库创建完成")
        return self.vectorstore

    def load_vectorstore(self) -> Chroma:
        """加载已有向量数据库。"""
        if not self.persist_directory.exists():
            raise FileNotFoundError(f"向量库目录不存在: {self.persist_directory}")

        logger.info(
            "加载向量数据库 collection={} path={}",
            self.collection_name,
            self.persist_directory,
        )

        self.vectorstore = Chroma(
            persist_directory=str(self.persist_directory),
            embedding_function=self.embeddings,
            collection_name=self.collection_name,
        )

        logger.info("向量数据库加载完成")
        return self.vectorstore

    def get_vectorstore(self) -> Chroma:
        """获取向量库实例；未创建时尝试从磁盘加载。"""
        if self.vectorstore is not None:
            return self.vectorstore

        try:
            return self.load_vectorstore()
        except Exception as exc:
            logger.warning("向量数据库未初始化或加载失败: {}", exc)
            raise RuntimeError("向量数据库未初始化，请先调用 create_vectorstore") from exc

    def add_documents(self, documents: list[Document]) -> list[str]:
        """向已有向量库追加文档。"""
        if not documents:
            return []
        store = self.get_vectorstore()
        ids = store.add_documents(documents)
        logger.info("向向量库追加 {} 篇文档", len(documents))
        return ids
