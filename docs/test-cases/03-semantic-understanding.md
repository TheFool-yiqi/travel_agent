# 语义理解测试用例

> **模块：** SEM · **用例数：** 55 · **版本：** v2.0 · **更新：** 2026-06-03

覆盖 `backend/app/graph/semantic/` 词表、澄清、防幻觉、`holiday_calendar`、`intent_normalizer`、`semantic_metrics` 等。

---

| 用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 |
|----------|----------|--------|------|--------|----------|----------|----------|----------|
| TC-SEM-001 | region_lexicon 省级区域识别 | P1 | 功能 | ✅ | — | 1. 输入「川西」/「长三角」 | 区域词 | 解析为区域候选；不当作 city |
| TC-SEM-002 | 错别字 typo_auto：程度→成都 | P0 | 功能 | ✅ | destination 步 | 1. 输入 `程度` | typo | action=clarify；候选成都 |
| TC-SEM-003 | typo 用户确认「对」 | P0 | 功能 | ✅ | pending clarify | 1. `程度` 2. `对` | E1 场景 | destination=成都；追问 departure_city |
| TC-SEM-004 | city_lexicon 精确匹配 | P0 | 功能 | ✅ | — | 1. resolve `成都` | 精确名 | action=accept；city=成都 |
| TC-SEM-005 | city_lexicon 别名匹配 | P1 | 功能 | ✅ | — | 1. 输入常见别名 | 如「蓉城」 | accept 或 clarify 至成都 |
| TC-SEM-006 | 西藏不误解析为西安 | P0 | 功能 | ✅ | — | 1. resolve `西藏` | 模糊 | accept；city=西藏；≠西安 |
| TC-SEM-007 | 天堂 fuzzy 需澄清 | P0 | 功能 | ✅ | — | 1. resolve `天堂` | 多义 | action=clarify；不自动绑天津 |
| TC-SEM-008 | 天水 vs 天津 消歧 | P1 | 功能 | ⏳ | — | 1. 分别输入 | 天水/天津 | 正确 city；不混淆 |
| TC-SEM-009 | place_lexicon 景点别名 | P1 | 功能 | ✅ | — | 1. 输入景点俗称 | 如「鸟巢」 | 映射至地点/城市上下文 |
| TC-SEM-010 | destination_resolver 分层策略 | P1 | 功能 | ✅ | — | 1. 测 exact/alias/typo/fuzzy 路径 | 多输入 | 各层返回预期 action |
| TC-SEM-011 | intent_normalizer 口语天数 | P0 | 功能 | ✅ | — | 1. normalize `玩三天` | 口语 | travel_days=3 |
| TC-SEM-012 | intent_normalizer 口语预算 | P0 | 功能 | ✅ | — | 1. normalize 档位词 | `一般党` | 映射 tier；仅用户提及后生效 |
| TC-SEM-013 | holiday_calendar 端午日期 | P0 | 功能 | ✅ | — | 1. 日期 2026-06-19 | 端午 | 识别节日名 |
| TC-SEM-014 | holiday_calendar 整个假期天数 | P0 | 功能 | ✅ | date=端午 | 1. `整个假期` | — | travel_days=3 |
| TC-SEM-015 | correction_handler 改目的地 | P1 | 功能 | ✅ | destination=北京 | 1. `不对，改成杭州` | 纠错 | destination→杭州 |
| TC-SEM-016 | correction_handler 改日期 | P2 | 功能 | ✅ | 有 departure_date | 1. `日期改到 7 月 1 日` | — | date 更新 |
| TC-SEM-017 | slot_sanitizer 出发目的地冲突 | P0 | 功能 | ✅ | 同值冲突 | 1. dest=成都, dep=成都 | — | 清除 departure_city；保留 destination |
| TC-SEM-018 | slot_sanitizer clarify 后绑定 | P0 | 功能 | ✅ | pending clarify 程度 | 1. 确认成都 | — | 仅 destination；不问重复 |
| TC-SEM-019 | disambiguator 预算每人/总共 | P0 | 功能 | ✅ | — | 1. `3000左右` | 歧义金额 | 触发 per_person vs total 澄清 |
| TC-SEM-020 | sanitize_budget 无用户提及清除 | P0 | 功能 | ✅ | LLM 幻觉字段 | 1. sanitize_budget | 对话无预算 | 移除 budget_min/max/tier |
| TC-SEM-021 | sanitize_travel_styles 无提及清除 | P0 | 功能 | ✅ | LLM 填 culture | 1. sanitize_travel_styles | 无风格词 | travel_styles 空 |
| TC-SEM-022 | sanitize_destination 非法值 | P1 | 功能 | ⏳ | — | 1. 输入非城市字符串 | `随便` | 不写入或 clarify |
| TC-SEM-023 | semantic_pipeline 端到端 | P1 | 功能 | ✅ | — | 1. 跑 pipeline | 典型句 | frame 含 slot_updates/trace |
| TC-SEM-024 | slot_tracker bind_utterance | P1 | 功能 | ✅ | — | 1. bind 各类输入 | 天堂 | clarify 时不写 destination |
| TC-SEM-025 | semantic_frame pending_clarification | P1 | 功能 | ✅ | clarify 后 | 1. 查 state | — | pending 结构含 slot/candidate |
| TC-SEM-026 | normalizer 数字中文 | P2 | 功能 | ✅ | — | 1. `三天` `两千` | — | 正确数值 |
| TC-SEM-027 | destination_semantics 区域推荐 | P2 | 功能 | ⏳ | 输入省/区域 | 1. `云南` | — | 可 accept 或推荐城市列表 |
| TC-SEM-028 | lexicon 扩展词条回归 | P2 | 回归 | ✅ | — | 1. test_lexicon_expansion | 新词 | 不破坏旧映射 |
| TC-SEM-029 | 拼音/简写 city | P2 | 功能 | ⏳ | — | 1. `bj` / `cd` | — | clarify 或 accept |
| TC-SEM-030 | 港澳台目的地 | P2 | 功能 | ❌ | — | 1. `香港` | — | 正确 accept |
| TC-SEM-031 | 国外目的地策略 | P2 | 功能 | ❌ | — | 1. `东京` | — | accept 或说明支持范围 |
| TC-SEM-032 | 连续 clarify 不栈溢出 | P2 | 异常 | ❌ | — | 1. 连续 5 次模糊输入 | — | 系统仍响应；不崩溃 |
| TC-SEM-033 | semantic_metrics 槽位命中率 | P1 | 接口 | ✅ | 会话有多轮 | 1. 聚合 metrics | — | hit_rate 等字段合理 |
| TC-SEM-034 | semantic_metrics API 鉴权 | P1 | 安全 | ✅ | — | 1. 无 Token 请求 | — | 401 |
| TC-SEM-035 | semantic_trace 写入消息 | P2 | 功能 | ✅ | pipeline 运行 | 1. 查 message metadata | — | trace 可提取 |
| TC-SEM-036 | oral_regression 口语综合 | P0 | 回归 | ✅ | — | 1. test_semantic_oral_regression | 多场景 | 全绿 |
| TC-SEM-037 | anti_hallucination 预算档位 | P0 | 功能 | ✅ | 未选预算 | 1. 检查确认块 | — | 无「一般党」 |
| TC-SEM-038 | anti_hallucination 旅行风格 | P0 | 功能 | ✅ | 未选风格 | 1. 最终确认 | — | 无 culture 等默认 |
| TC-SEM-039 | 用户否定 clarify 候选 | P1 | 功能 | ❌ | 程度→成都? | 1. `不是` | — | 重新询问目的地 |
| TC-SEM-040 | 多槽同句纠错优先级 | P2 | 功能 | ⏳ | 多槽已填 | 1. `出发地改成南京` | — | 仅 departure_city 更新 |
| TC-SEM-041 | bind 空 utterance | P3 | 异常 | ❌ | — | 1. 空字符串 | — | 无 slot_updates |
| TC-SEM-042 | resolver 大小写不敏感 | P2 | 功能 | ⏳ | — | 1. `Beijing` | — | accept 北京 |
| TC-SEM-043 | 重复 clarify 同一 slot | P2 | 异常 | ❌ | — | 1. 两次 `天堂` | — | 不重复 bind 错误值 |
| TC-SEM-044 | metrics 澄清轮次计数 | P1 | 功能 | ✅ | 有 clarify 轮 | 1. aggregate | — | clarification_turns≥1 |
| TC-SEM-045 | pipeline 与 collect 节点集成 | P0 | 功能 | ✅ | 真实 graph | 1. 发「程度」 | — | 助手澄清；state 一致 |
| TC-SEM-046 | destination_resolution_policy | P0 | 回归 | ✅ | — | 1. test_destination_resolution_policy | 策略表 | 全绿 |
| TC-SEM-047 | 模糊词「帝都」 | P2 | 功能 | ⏳ | — | 1. 输入 `帝都` | 别名 | →北京 |
| TC-SEM-048 | 模糊词「魔都」 | P2 | 功能 | ⏳ | — | 1. `魔都` | — | →上海 |
| TC-SEM-049 | slot 冲突后 guidance_step | P1 | 功能 | ✅ | sanitize 后 | 1. 查 guidance_step | — | 指向下一缺失槽 |
| TC-SEM-050 | LLM extract 与 sanitizer 顺序 | P1 | 功能 | ⏳ | — | 1. extract→sanitize | — | 幻觉被 sanitizer 清除 |
| TC-SEM-051 | 预算 tier 穷游/一般/轻奢 | P1 | 功能 | ✅ | — | 1. 各档位词 | 三档 | min/max 正确 |
| TC-SEM-052 | party 口语「一家三口」 | P1 | 功能 | ⏳ | party 步 | 1. `一家三口` | — | 2 成人 1 儿童或 clarify |
| TC-SEM-053 | 日期相对「下周五」 | P2 | 功能 | ⏳ | 有 get_current_date | 1. `下周五` | — | 解析为具体 ISO |
| TC-SEM-054 | semantic 性能 <500ms 词表 | P3 | 性能 | ❌ | — | 1. 100 次 resolve | — | P95 在阈值内 |
| TC-SEM-055 | 导出 metrics JSON schema | P2 | 接口 | ✅ | — | 1. 校验 SemanticMetricsResponse | — | 符合 pydantic schema |

### TC-SEM-002 / TC-SEM-007 扩展说明（P0）

**E1 错别字（smoke exception-path）：**

1. 用户：`程度` → 助手澄清「是否成都？」
2. 用户：`对` → `destination=成都`，追问出发城市
3. 用户：`上海` → `departure_city=上海`，destination 保持成都

**天堂模糊（smoke）：**

- `resolve_destination_input("天堂").action == "clarify"`
- `bind_utterance_to_slots` 不产生 destination 更新

---

## 自动化映射

| 测试文件 | 覆盖用例 |
|----------|----------|
| `test_destination_resolution_policy.py` | TC-SEM-046 |
| `test_city_lexicon.py` / `test_place_lexicon.py` | TC-SEM-004~009 |
| `test_smoke_flows.py` (smoke_exception) | TC-SEM-002~003, 006~007, 014, 017~018, 020~021 |
| `test_correction_handler.py` | TC-SEM-015~016 |
| `test_slot_sanitizer.py` | TC-SEM-017~018 |
| `test_holiday_dates.py` | TC-SEM-013~014 |
| `test_intent_normalizer.py` | TC-SEM-011~012 |
| `test_semantic_metrics_api.py` | TC-SEM-033~034, 055 |
| `e2e/exception-path.spec.ts` | TC-SEM-002~003（部分） |

## 流程关联

- FLOW-07：TC-SEM-002~003
- FLOW-08：TC-SEM-006~008
- FLOW-10：TC-SEM-011~014
- FLOW-11：TC-SEM-015
