# 词表扩展指南

旅行 Agent 的地名理解依赖三层词表，扩展时请按层级维护。

## 三层结构

| 层级 | 文件 | 适用输入 | 示例 |
|------|------|----------|------|
| **区域** | `backend/app/graph/semantic/region_lexicon.py` | 省/自治区/口语区域 | 西藏、南疆、川西 |
| **城市** | `backend/app/graph/semantic/city_lexicon.py` | 城市名、昵称、错字 | 成都、程度→成都 |
| **景点** | `backend/app/graph/semantic/place_lexicon.py` | 景区/地标简称 | 洱海→大理、兵马俑→西安 |

解析顺序：**区域 → 景点 → 城市（精确/白名单错字）→ 模糊（仅澄清，不自动采纳）**

详见 [destination-resolution-policy.md](./destination-resolution-policy.md)。

---

## 1. 扩展区域词表

```python
# region_lexicon.py
REGION_DESTINATIONS: frozenset[str] = frozenset({
    "西藏",
    # 新增省/自治区名 …
})

REGION_ALIASES: dict[str, str] = {
    "南疆": "新疆",
    # 口语简称 → 规范区域名
}
```

**适用：** 用户说「西藏」「川西」「南疆」等，整句等于区域名。

**不适用：** 具体城市（放 city_lexicon）、单个景点（放 place_lexicon）。

---

## 2. 扩展城市词表

```python
CityEntry(
    "敦煌",           # 规范城市名（写入 destination）
    "dunhuang",       # 拼音（预留）
    ("沙州",),        # aliases：昵称、简称，精确匹配可 accept
    ("燉煌",),        # typos_confirm：同音/近音，需用户确认
    ("敦煌",),        # typos_auto：形近错字，高置信自动纠正（慎用）
)
```

| 字段 | 含义 | 行为 |
|------|------|------|
| `aliases` | 别名 | 精确匹配 → 直接采纳 |
| `typos_confirm` | 需确认错字 | 「你是说 XX 吗？」 |
| `typos_auto` | 白名单自动纠正 | 仅明显形近错字（如 杭洲→杭州） |

**不要**把不同含义的地名放进 `typos_auto`（如 西藏≠西安）。

---

## 3. 扩展景点词表

```python
# place_lexicon.py
PLACE_ALIASES: dict[str, str] = {
    "赛里木湖": "伊犁",   # 别名 → 规划用目的地（通常是城市/景区所在市）
    "故宫": "北京",
}
```

**canonical 目标** 优先选 `city_lexicon` 中已有的城市名，便于后续交通/酒店查询。

**注意：** 键越长越优先（子串匹配时）；避免过短键（如单独「山」）造成误匹配。

---

## 4. 测试

新增条目后请补充测试：

```bash
# 城市 / 景点
uv run pytest backend/tests/test_city_lexicon.py backend/tests/test_place_lexicon.py -q

# 解析策略（含 西藏≠西安）
uv run pytest backend/tests/test_destination_resolution_policy.py -q

# 口语回归（可选，加 parametrize case）
uv run pytest backend/tests/test_semantic_oral_regression.py -q
```

---

## 5. 本次扩展摘要（2026-06）

- **城市 +45**：西北/西南/华东/华南热门目的地及常见错字
- **区域别名 +8**：藏区、南疆/北疆、川西、黔东南/黔西南等
- **景点 +120**：一线地标、5A 景区、网红打卡点 → 所在城市

如需继续扩展，建议按 **目的地文档** 或 **用户日志高频未识别词** 批量导入，而非一次性穷举全国区县。
