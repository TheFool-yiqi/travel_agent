"""父文档索引持久化读写。"""

from __future__ import annotations

import json
from pathlib import Path

from app.settings import BASE_DIR

_PARENT_STORE = Path(BASE_DIR) / "data" / "vectorstore" / "parent_docs.jsonl"


def load_parent_index() -> dict[str, str]:
    index: dict[str, str] = {}
    if not _PARENT_STORE.is_file():
        return index
    with _PARENT_STORE.open(encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            parent_id = record.get("parent_id")
            if parent_id:
                index[str(parent_id)] = record.get("page_content", "")
    return index
