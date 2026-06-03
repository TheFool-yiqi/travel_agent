"""目的地本地攻略文件解析。"""

from __future__ import annotations

from pathlib import Path

from app.settings import BASE_DIR

_DOCS_DIR = Path(BASE_DIR) / "data" / "documents" / "destinations"

_DESTINATION_FILES: dict[str, str] = {
    "西安": "xian-travel-guide",
    "xian": "xian-travel-guide",
    "成都": "chengdu-travel-guide",
    "chengdu": "chengdu-travel-guide",
    "长沙": "changsha-travel-guide",
    "changsha": "changsha-travel-guide",
    "杭州": "hangzhou-travel-guide",
    "hangzhou": "hangzhou-travel-guide",
    "大理": "dali-lijiang-travel-guide",
    "丽江": "dali-lijiang-travel-guide",
    "dali": "dali-lijiang-travel-guide",
    "lijiang": "dali-lijiang-travel-guide",
    "重庆": "chongqing-travel-guide",
    "chongqing": "chongqing-travel-guide",
    "厦门": "xiamen-travel-guide",
    "xiamen": "xiamen-travel-guide",
    "鼓浪屿": "xiamen-travel-guide",
    "桂林": "guilin-yangshuo-travel-guide",
    "阳朔": "guilin-yangshuo-travel-guide",
    "guilin": "guilin-yangshuo-travel-guide",
    "yangshuo": "guilin-yangshuo-travel-guide",
    "苏州": "suzhou-travel-guide",
    "suzhou": "suzhou-travel-guide",
    "北京": "beijing-travel-guide",
    "beijing": "beijing-travel-guide",
    "上海": "shanghai-travel-guide",
    "shanghai": "shanghai-travel-guide",
}


def resolve_guide_path(destination: str) -> Path | None:
    key = destination.strip().lower()
    for alias, stem in _DESTINATION_FILES.items():
        if alias.lower() in key or key in alias.lower():
            path = _DOCS_DIR / f"{stem}.md"
            if path.is_file():
                return path
    return None


def read_destination_guide(destination: str) -> str | None:
    path = resolve_guide_path(destination)
    if path is None:
        return None
    return path.read_text(encoding="utf-8")
