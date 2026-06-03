"""父文档上下文映射（兼容别名，请优先使用 AdvancedParentDocumentSplitter）。"""

from __future__ import annotations

from app.knowledge.document_splitter import AdvancedParentDocumentSplitter

ParentContextMapper = AdvancedParentDocumentSplitter

__all__ = ["AdvancedParentDocumentSplitter", "ParentContextMapper"]
