"""RAG 知识层：文档加载与预处理。"""

from __future__ import annotations

import re
from pathlib import Path

from langchain_core.documents import Document
from loguru import logger

from app.settings import BASE_DIR

_CITY_RE = re.compile(r"^city:\s*(.+)$", re.MULTILINE)


class DocumentManager:
    """从 data/documents/ 加载 Markdown 文档并附加 RAG 元数据。"""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = (
            Path(base_dir) if base_dir is not None else Path(BASE_DIR) / "data" / "documents"
        )

    def load_destination_documents(self) -> list[Document]:
        """加载 destinations/ 下的目的地攻略。"""
        return self._load_category_documents(
            category="destinations",
            source_type="destination_guide",
        )

    def load_food_documents(self) -> list[Document]:
        """加载 food/ 下的美食文档。"""
        return self._load_category_documents(
            category="food",
            source_type="food_guide",
        )

    def load_accommodation_documents(self) -> list[Document]:
        """加载 accommodation/ 下的住宿文档。"""
        return self._load_category_documents(
            category="accommodation",
            source_type="accommodation_guide",
        )

    def load_all_documents(self) -> list[Document]:
        """加载所有已配置分类的文档。"""
        loaders = (
            self.load_destination_documents,
            self.load_food_documents,
            self.load_accommodation_documents,
        )
        documents: list[Document] = []
        for loader in loaders:
            documents.extend(loader())
        return documents

    def _load_category_documents(self, category: str, source_type: str) -> list[Document]:
        category_dir = self.base_dir / category

        if not category_dir.exists():
            logger.warning("文档目录不存在: {}", category_dir)
            return []

        documents: list[Document] = []
        for path in sorted(category_dir.rglob("*.md")):
            if path.name.lower() == "readme.md":
                continue

            text = path.read_text(encoding="utf-8")
            metadata = {
                "source": str(path),
                "source_type": source_type,
                "category": category,
                "slug": path.stem,
            }

            city_match = _CITY_RE.search(text)
            if city_match:
                metadata["city"] = city_match.group(1).strip()

            documents.append(Document(page_content=text, metadata=metadata))

        logger.info("从 {} 加载了 {} 个 {} 文档", category_dir, len(documents), category)
        return documents
