"""省级行政区 / 区域目的地（精确匹配，不参与城市模糊纠错）。"""

from __future__ import annotations

# 用户常作为「目的地」输入的省级/区域名（整句精确匹配）
REGION_DESTINATIONS: frozenset[str] = frozenset(
    {
        "西藏",
        "新疆",
        "内蒙古",
        "内蒙",
        "宁夏",
        "广西",
        "香港",
        "澳门",
        "台湾",
        "海南",
        "云南",
        "贵州",
        "青海",
        "甘肃",
        "黑龙江",
        "吉林",
        "辽宁",
        "河北",
        "山西",
        "山东",
        "河南",
        "湖北",
        "湖南",
        "安徽",
        "江西",
        "江苏",
        "浙江",
        "福建",
        "广东",
        "陕西",
        "四川",
    },
)

# 别名 → 规范区域名
REGION_ALIASES: dict[str, str] = {
    "内蒙": "内蒙古",
    "藏区": "西藏",
    "南疆": "新疆",
    "北疆": "新疆",
    "东疆": "新疆",
    "川西": "四川",
    "黔西南": "贵州",
    "黔东南": "贵州",
}


def lookup_region(text: str) -> str | None:
    """整句精确匹配区域/省名，返回规范名称。"""
    key = text.strip()
    if not key:
        return None
    if key in REGION_DESTINATIONS:
        return REGION_ALIASES.get(key, key)
    return REGION_ALIASES.get(key)


def is_region_destination(text: str) -> bool:
    return lookup_region(text) is not None
