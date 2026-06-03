# 需求收集测试用例

> **模块：** REQ · **用例数：** 45 · **版本：** v2.0 · **更新：** 2026-06-03

覆盖 `collect_requirements` 节点、`collect_guidance.py` 七步引导、`validators/requirements.py` 及 LLM 抽取链路。

**引导顺序：** destination → departure_city → departure_date → travel_days → party → budget → confirm（done）

---

| 用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 |
|----------|----------|--------|------|--------|----------|----------|----------|----------|
| TC-REQ-001 | 首步引导询问目的地 | P0 | 功能 | ✅ | 新会话；fields 空 | 1. 发送任意首条消息或等待问候后回复 | — | `next_guidance_step`=`destination`；追问目的地 |
| TC-REQ-002 | 填写目的地后引导出发城市 | P0 | 功能 | ✅ | destination 已填 | 1. 输入目的地 | `北京` | 下一步=`departure_city`；不跳步 |
| TC-REQ-003 | 出发城市后引导出发日期 | P0 | 功能 | ✅ | 目的地+出发城市 | 1. 输入出发城市 | `上海` | 下一步=`departure_date` |
| TC-REQ-004 | 多轮跨槽位补全（成都→上海→日期） | P0 | 功能 | ⏳ | 新会话 | 1. `成都` 2. `上海` 3. `2026-07-01` | 跨槽输入 | destination=成都；departure_city=上海；date 正确；不丢槽 |
| TC-REQ-005 | 日期识别后引导天数 | P0 | 功能 | ✅ | 前三槽已满 | 1. 输入日期 | `2026-06-19` | 识别端午节；下一步=`travel_days` |
| TC-REQ-006 | 天数后引导人数 party | P0 | 功能 | ✅ | 日期+天数已填 | 1. 输入天数 | `3天` | 下一步=`party`；**不出现**预算档位 |
| TC-REQ-007 | 人数确认后引导预算 | P0 | 功能 | ✅ | party_confirmed | 1. 输入人数 | `就我一个人` | 下一步=`budget` |
| TC-REQ-008 | 预算填完后进入确认 | P0 | 功能 | ✅ | 预算 min/max 已填 | 1. 输入预算档位 | `穷游党` | `next_guidance_step`=`done`；展示需求摘要 |
| TC-REQ-009 | 用户确认「对的」推进规划 | P0 | 功能 | ✅ | 摘要已展示 | 1. 发送确认 | `对的` | `user_confirmed=true`；路由至 `plan_destination` |
| TC-REQ-010 | 未确认前不进入 plan_destination | P0 | 功能 | ✅ | requirements_complete 但未确认 | 1. 检查 route_after_collect | user_confirmed=false | 返回 `__end__` 等待用户 |
| TC-REQ-011 | 七步顺序不可跳过 | P0 | 功能 | ✅ | 空 fields | 1. 逐步填满 2. 每步断言 guidance | 主路径数据 | 严格 destination→…→budget→done |
| TC-REQ-012 | 并行抽取：一句多槽 | P1 | 功能 | ⏳ | 在 destination 步 | 1. 发送「上海出发去北京」 | 组合句 | 可同时填 departure_city+destination；仍按 guidance 追问缺失项 |
| TC-REQ-013 | 缺 departure_city 不进入日期步 | P1 | 功能 | ✅ | 仅有 destination | 1. 检查 guidance | destination=北京 | 仍问出发城市 |
| TC-REQ-014 | 缺 travel_days 不进入 party | P1 | 功能 | ✅ | 有 date 无 days | 1. 检查 guidance | — | 仍问天数 |
| TC-REQ-015 | party 未 confirmed 不进入 budget | P1 | 功能 | ✅ | adult_count 有值但 party_confirmed=false | 1. 检查 guidance | — | 仍问人数 |
| TC-REQ-016 | 预算未填 min/max 不 done | P0 | 功能 | ✅ | 仅 budget_tier 无 min/max | 1. sanitize + guidance | — | 仍处 budget 步 |
| TC-REQ-017 | 确认摘要单段不重复 | P0 | 功能 | ✅ | 进入最终确认 | 1. 读助手消息 | — | 仅一段「我整理一下您的需求」；不与【当前已确认】重复 |
| TC-REQ-018 | 【当前已确认】块字段完整 | P1 | 功能 | ⏳ | 各槽已填 | 1. 查看确认块 | 主路径 | 含目的地/出发/日期/天数/人数/预算 |
| TC-REQ-019 | 用户否认摘要重新收集 | P1 | 功能 | ❌ | 展示摘要 | 1. 发送「不对，改一下」 | 否定句 | 保持 collect；追问需修改项 |
| TC-REQ-020 | 纯寒暄不触发 LLM 抽取 | P1 | 功能 | ✅ | 在 collection 步 | 1. 发送「你好呀」 | 寒暄 | 友好回复；不写入虚假槽位 |
| TC-REQ-021 | 问候 bootstrap 仅新会话 | P1 | 功能 | ✅ | 新 session | 1. 创建会话 | — | seed_initial_greeting 一条 |
| TC-REQ-022 | inject_user_memory 不影响引导顺序 | P2 | 功能 | ⏳ | 用户有历史偏好 | 1. 新行程收集 | — | guidance 顺序不变；记忆仅注入 prompt |
| TC-REQ-023 | semantic_pipeline 与 guidance 协同 | P1 | 功能 | ✅ | 任意输入 | 1. 发送用户句 2. 查 frame | `程度` | pipeline 产出 clarify；guidance 不跳步 |
| TC-REQ-024 | 出发日期非法格式澄清 | P1 | 异常 | ⏳ | 问日期时 | 1. 输入 `明天吧看看` | 模糊日期 | 澄清或 LLM 辅助；不写入无效 ISO |
| TC-REQ-025 | 天数口语「整个假期」 | P0 | 功能 | ✅ | departure_date=2026-06-19 | 1. 输入 `整个假期` | 端午 | travel_days=3；继续 party |
| TC-REQ-026 | 天数无法理解兜底 | P1 | 异常 | ⏳ | 问天数 | 1. `看情况吧` | 模糊 | LLM 澄清或建议；不无限重复同问句 |
| TC-REQ-027 | 人数口语「两大一小」 | P1 | 功能 | ⏳ | 问 party | 1. `两大一小` | — | adult=2, children=1；party_confirmed |
| TC-REQ-028 | 预算档位穷游党映射 | P0 | 功能 | ✅ | 问 budget | 1. `穷游党` | 档位词 | budget_min/max 落入对应 tier |
| TC-REQ-029 | 预算金额「3000左右」歧义 | P0 | 功能 | ✅ | 问 budget | 1. `3000左右` | — | 追问「每人还是总共」 |
| TC-REQ-030 | 预算防幻觉：未说则不填 | P0 | 功能 | ✅ | 未问 budget 前 | 1. sanitize_budget | 对话无预算词 | 无 budget_min/tier |
| TC-REQ-031 | 旅行风格防幻觉 | P0 | 功能 | ✅ | 未提风格 | 1. sanitize_travel_styles | — | travel_styles 空 |
| TC-REQ-032 | 确认前 progress 停需求阶段 | P0 | UI | ✅ | 收集中 | 1. 观察 StepProgress | — | current=`collect_requirements` |
| TC-REQ-033 | 确认后 progress 进目的地 | P0 | UI | ⏳ | 用户确认 | 1. 发送「对的」 | — | progress→`plan_destination` |
| TC-REQ-034 | collect_reply 校验助手回复 | P2 | 功能 | ✅ | mock LLM | 1. 跑 collect_reply validator | — | 违规回复被拦截/重写 |
| TC-REQ-035 | requirements_complete 门槛 | P1 | 功能 | ✅ | 缺任一项 | 1. 检查 complete 标志 | 缺 budget | requirements_complete=false |
| TC-REQ-036 | user_requirement 结构持久化 | P1 | 功能 | ⏳ | 确认后 | 1. 查 state/checkpoint | — | user_requirement dict 完整 |
| TC-REQ-037 | 重复发送同一槽位更新 | P2 | 功能 | ❌ | 已有 destination | 1. 再说「改成杭州」 | 纠错 | destination 更新；见 TC-SEM 纠错 |
| TC-REQ-038 | 儿童数为 0 的单身出行 | P2 | 功能 | ✅ | party 步 | 1. `1个人` | — | adult=1, children=0 |
| TC-REQ-039 | 超长目的地输入截断/澄清 | P2 | 异常 | ❌ | destination 步 | 1. 输入 500 字 | 超长 | 不崩溃；澄清或截取 |
| TC-REQ-040 | 英文混合输入 | P2 | 功能 | ⏳ | 任意步 | 1. `Beijing 3 days` | 中英混 | 尽量抽取；guidance 补中文缺失 |
| TC-REQ-041 | 连续快速发送合并 | P2 | 异常 | ❌ | 收集中 | 1. 200ms 内连发 3 条 | — | 不丢消息；顺序处理 |
| TC-REQ-042 | SSE 流式 collect 回复 | P1 | 接口 | ✅ | 已登录会话 | 1. POST `/chat/stream/{id}` | 任意输入 | SSE token 流；最终消息入库 |
| TC-REQ-043 | 主路径冒烟数据全链路 | P0 | 回归 | ✅ | 新会话 | 1. 按 smoke main-path 7 步输入 | 北京/上海/2026-06-19/3天/1人/穷游党/对的 | 进入 plan_destination |
| TC-REQ-044 | awaiting_confirmation 时不 followup | P1 | 功能 | ✅ | 等待确认 | 1. needs_guidance_followup(awaiting=true) | — | 返回 false |
| TC-REQ-045 | done 后不再 guidance followup | P1 | 功能 | ✅ | 所有槽满 | 1. needs_guidance_followup | — | 返回 false |

### TC-REQ-004 扩展说明（P0 · FLOW-09）

- **场景：** 用户先答目的地，再答出发城市，再答日期（跨轮跨槽）。
- **关联：** `test_smoke_flows.py::test_guidance_after_departure_city_keeps_destination`
- **预期：** `destination=成都` 在填 `上海` 后仍保留；`departure_city=上海`；日期写入后进入 travel_days。

---

## 自动化映射

| 测试文件 | 覆盖用例 |
|----------|----------|
| `test_smoke_flows.py` (smoke_main) | TC-REQ-002~011, 043 |
| `test_collect_requirements.py` | TC-REQ-017, 030~031 |
| `test_collect_guidance.py` | TC-REQ-001~008 |
| `test_collect_requirements_greeting.py` | TC-REQ-020~021 |
| `test_user_confirmed_gate.py` | TC-REQ-009~010 |
| `e2e/main-path.spec.ts` | TC-REQ-043 |

## 流程关联

- FLOW-02：TC-REQ-001~009
- FLOW-09：TC-REQ-004
- FLOW-10：TC-REQ-025~029
- FLOW-14：TC-REQ-020
