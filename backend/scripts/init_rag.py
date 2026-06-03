"""
初始化 RAG 系统：加载文档 → 切分 → 创建 Chroma 向量库

用法（在 backend 目录）：
    uv run python scripts/init_rag.py
"""
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from loguru import logger

from app.knowledge import DocumentManager, ParentDocumentSplitter, VectorStoreManager
from app.settings import settings
from app.utils.logging import setup_logger

setup_logger()

_PARENT_STORE_FILENAME = "parent_docs.jsonl"


def _save_parent_docs(parent_docs, persist_directory: Path) -> Path:
    """将父文档索引写入向量库目录，供检索后回填上下文。"""
    path = persist_directory / _PARENT_STORE_FILENAME
    with path.open("w", encoding="utf-8") as file:
        for doc in parent_docs:
            record = {
                "parent_id": doc.metadata.get("parent_id"),
                "page_content": doc.page_content,
                "metadata": doc.metadata,
            }
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def main() -> None:
    logger.info("开始初始化 RAG 系统...")

    if not settings.dashscope_api_key:
        logger.error("DASHSCOPE_API_KEY 未配置，无法创建嵌入向量")
        sys.exit(1)

    logger.info("加载文档...")
    doc_manager = DocumentManager()
    documents = doc_manager.load_destination_documents()

    if not documents:
        logger.error("未找到文档，请先添加文档到 data/documents/destinations/")
        sys.exit(1)

    logger.info("切分文档...")
    splitter = ParentDocumentSplitter()
    parent_docs, child_docs = splitter.split_documents(documents)

    logger.info("创建向量数据库（使用子文档索引）...")
    vs_manager = VectorStoreManager()
    vs_manager.create_vectorstore(child_docs)

    parent_store_path = _save_parent_docs(parent_docs, vs_manager.persist_directory)

    logger.info("RAG 系统初始化完成")
    logger.info("  源文档数量: {}", len(documents))
    logger.info("  父文档数量: {}", len(parent_docs))
    logger.info("  子文档数量: {}", len(child_docs))
    logger.info("  向量库路径: {}", vs_manager.persist_directory)
    logger.info("  父文档索引: {}", parent_store_path)


if __name__ == "__main__":
    main()
