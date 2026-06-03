# 目的地解析策略

防止「西藏 → 西安」类误匹配的系统方案，与预算/旅行风格防幻觉同一思路。

## 分层策略

| 层级 | 模块 | 规则 |
|------|------|------|
| L1 区域 | `region_lexicon.py` | 省/自治区整句精确匹配，优先于城市模糊 |
| L2 景点 | `place_lexicon.py` | 别名精确匹配 |
| L3 城市 | `city_lexicon.py` | 精确 / 别名 / **白名单** typo_auto 可自动采纳 |
| L4 模糊 | `city_lexicon.match_cities` | **一律 `needs_confirm=True`**，禁止静默改写 |
| L5 合并 | `destination_resolver.py` | `fuzzy` 源只输出 `clarify`，不 `accept` |
| L6 防幻觉 | `sanitize_destination()` | 用户原话与 destination 不一致且无确认 → 剥离 |
| L7 LLM | `merge_extraction` | 在 `destination` 引导步忽略 LLM 写入的目的地 |

## 行为对照

| 用户输入 | 旧行为 | 新行为 |
|----------|--------|--------|
| 西藏 | 模糊 → 西安（自动） | 区域精确 → 西藏 |
| 程度 | 澄清 → 成都 | 不变（typo_confirm） |
| 杭洲 | 自动 → 杭州 | 不变（typo_auto 白名单） |
| 西按 | 可能 → 西安 | 澄清确认 |

## 扩展

- 新增区域：写入 `REGION_DESTINATIONS`
- 新增可自动纠正错字：写入 `CityEntry.typos_auto`
- 需确认的错字：写入 `typos_confirm`
- **维护指南：** [lexicon-extension.md](./lexicon-extension.md)

## 测试

- `tests/test_destination_resolution_policy.py`
- `tests/test_smoke_flows.py::test_xizang_not_resolved_to_xian`
