# PlanningRuntime 九阶段测试用例（TC-RT-*）

> **模块：** Runtime Stages · **编号：** TC-RT-{STAGE}-{NNN}  
> **架构：** collect → prepare_base_context → retrieve_evidence → tool_enrich → domain_plan → integrate → verify → approve_or_revise → finalize  
> **自动化：** 见 [00-ai-manifest.json](./00-ai-manifest.json) · 执行：`uv run python scripts/run_test_case.py --suite SUITE-RUNTIME`

---

## 1. 用例字段说明

| 字段 | 说明 |
|------|------|
| **成功指标** | 可观测、可断言的 PASS 条件（pytest exit 0 + 下列条目） |
| **AI 命令** | manifest 中 `command` 数组，可直接 subprocess |
| **legacy_ids** | 替代的旧 TC-PLAN / TC-APR 编号 |

---

## 2. collect（TC-RT-COLLECT）

| 编号 | 名称 | 优先级 | 前置条件 | 步骤 | 成功指标 | AI 命令 |
|------|------|--------|----------|------|----------|---------|
| TC-RT-COLLECT-001 | 纯寒暄不触发规划 | P0 | 空 trip_spec | 1. 输入「你好」 2. 跑 collect policy | `planning_need` 为空；`awaiting_user=true` | `test_greeting_policy_blocks_planning_on_first_greeting` |
| TC-RT-COLLECT-002 | greeting 不含 planning 字段 | P1 | — | 调用 greeting_responder | 响应 JSON 无 destination/date 等 planning 字段 | `test_greeting_responder_does_not_emit_planning_need_fields` |
| TC-RT-COLLECT-003 | 未确认不能 ready | P0 | 槽位满但未确认 | readiness 检查 | `ready_for_planning=false` | `test_readiness_requires_confirmation_before_planning` |
| TC-RT-COLLECT-004 | 未确认 discovery 拒绝 | P1 | hypothesis 未确认 | readiness 检查 | 拒绝进入 domain_plan | `test_readiness_rejects_unconfirmed_discovery_hypothesis` |
| TC-RT-COLLECT-005 | runtime 寒暄轮 waiting | P0 | stub collect | 跑 collect stage | `stage_status=waiting`；无后续 stage 事件 | `test_collect_runtime_greeting_turn_waits_without_planning_need` |
| TC-RT-COLLECT-006 | 不完整 trip_spec 等待 | P0 | 缺 budget | 跑 collect stage | 停止在 collect；emit waiting | `test_collect_runtime_incomplete_trip_spec_waits` |

**多轮集成（补充）**

| 编号 | 名称 | 成功指标 |
|------|------|----------|
| TC-RT-COLLECT-007 | 首轮 collect 停止 | `test_planning_runtime_stops_on_first_collect_waiting_turn` — 仅 1 个 collect stage 对 |
| TC-RT-COLLECT-008 | 多轮 collect 至 planning_need | `test_multiturn_collect_reaches_planning_need_and_base_context` — 出现 planning_need + base_context |
| TC-RT-COLLECT-009 | ready 后进入 prepare…finalize 骨架 | `test_collect_ready_path_runs_prepare_base_context_and_skeleton_finalize` |

---

## 3. prepare_base_context（TC-RT-PREP）

| 编号 | 名称 | 优先级 | 成功指标 |
|------|------|--------|----------|
| TC-RT-PREP-001 | 从 planning_need 构建 context | P0 | `agent_context` 含 destination/dates/party/budget |
| TC-RT-PREP-002 | 无 planning_need 失败 | P1 | stage 失败；`runtime_failed` |
| TC-RT-PREP-003 | 不读 collect_context 私有字段 | P1 | 仅经 planning_need 边界读入 |
| TC-RT-PREP-004 | 注入 memory snippets | P2 | memory 出现在 prompt context |

---

## 4. retrieve_evidence（TC-RT-EVID）

| 编号 | 名称 | 优先级 | 成功指标 |
|------|------|--------|----------|
| TC-RT-EVID-001 | 写入 evidence_context | P0 | `evidence_context.cards` 非空或 sufficiency 标记 |
| TC-RT-EVID-002 | 无 planning_need 失败 | P1 | stage 失败 |
| TC-RT-EVID-003 | 不越界读 collect_context | P1 | 无 direct collect 依赖 |

---

## 5. tool_enrich（TC-RT-TOOL）

| 编号 | 名称 | 优先级 | 成功指标 |
|------|------|--------|----------|
| TC-RT-TOOL-001 | 写入 tool_context | P0 | `tool_context.weather` 或等价键存在 |
| TC-RT-TOOL-002 | 天气不可用降级 | P1 | stage 仍 completed；无 uncaught exception |
| TC-RT-TOOL-003 | 无 planning_need 失败 | P1 | stage 失败 |

---

## 6. domain_plan（TC-RT-DOMAIN）

| 编号 | 名称 | 优先级 | legacy | 成功指标 |
|------|------|--------|--------|----------|
| TC-RT-DOMAIN-001 | 产出 plan_proposals | P0 | TC-PLAN-006 | `plan_proposals` 含 destination/transport/stay/activity |
| TC-RT-DOMAIN-002 | 无 planning_need 失败 | P1 | — | stage 失败 |
| TC-RT-DOMAIN-003 | DomainPlannerGroup 冒烟 | P1 | — | `test_domain_planning_smoke` 全 PASS |
| TC-RT-DOMAIN-004 | 交通/食宿/活动枚举合法 | P0 | TC-PLAN-011~019 | proposal 内 enum ∈ VALID_* 集合 |

---

## 7. integrate（TC-RT-INTEG）

| 编号 | 名称 | 优先级 | legacy | 成功指标 |
|------|------|--------|--------|----------|
| TC-RT-INTEG-001 | 写入 itinerary_draft | P0 | TC-PLAN-023 | `days[].day_number` 连续；含 budget |
| TC-RT-INTEG-002 | 无 proposals 失败 | P1 | — | stage 失败 |
| TC-RT-INTEG-003 | 预算拆分结构 | P1 | TC-PLAN-024 | budget 含 transport/accommodation/food/attractions |

---

## 8. verify（TC-RT-VERIFY）

| 编号 | 名称 | 优先级 | 成功指标 |
|------|------|--------|----------|
| TC-RT-VERIFY-001 | 写入 quality_report | P0 | `quality_report.issues` 为列表 |
| TC-RT-VERIFY-002 | blocking 自动修订 | P1 | 触发 auto_revision；itinerary 更新 |
| TC-RT-VERIFY-003 | 无 draft 失败 | P1 | stage 失败 |

---

## 9. approve_or_revise（TC-RT-APPROVE）

| 编号 | 名称 | 优先级 | legacy | 成功指标 |
|------|------|--------|--------|----------|
| TC-RT-APPROVE-001 | 无关键词则等待 | P0 | TC-APR-001 | `awaiting_user=true`；emit approval_required |
| TC-RT-APPROVE-002 | 用户修订重开审批 | P0 | TC-APR-004 | 修订后重新 emit itinerary + approval_required |
| TC-RT-APPROVE-003 | 确认关键词完成 | P0 | TC-APR-002 | `approval_status=approved` |
| TC-RT-APPROVE-004 | 「再看看」非确认 | P1 | TC-APR-011 | `user_wants_revision` 为 false |

---

## 10. finalize（TC-RT-FINAL）

| 编号 | 名称 | 优先级 | legacy | 成功指标 |
|------|------|--------|--------|----------|
| TC-RT-FINAL-001 | 生成 ORDER 并持久化 | P0 | TC-FLOW-020 | 消息含 `ORDER-`；itinerary 入库 |
| TC-RT-FINAL-002 | 未审批失败 | P1 | — | finalize 不执行；runtime_failed 或 guard |

---

## 11. 编排器（TC-RT-ORCH）

| 编号 | 名称 | 优先级 | 成功指标 |
|------|------|--------|----------|
| TC-RT-ORCH-001 | 九阶段成对事件 | P0 | 9× stage_started + stage_completed + runtime_completed |
| TC-RT-ORCH-002 | handler 顺序 | P0 | 与 `V1_STAGE_NAMES` 一致 |
| TC-RT-ORCH-003 | collect 等待时停止 | P0 | 后续 stage 事件数为 0 |
| TC-RT-ORCH-004 | stage_outputs 传递 | P1 | 下游 handler 可读上游 output |
| TC-RT-ORCH-005 | 失败 emit runtime_failed | P1 | 流水线终止 |

---

## 12. 阶段骨架（横切）

| 编号 | 名称 | 成功指标 |
|------|------|----------|
| TC-RT-SKELETON-001 | 各 handler 返回匹配 stage 名 | `test_all_stage_handlers_return_matching_stage_names` |
| TC-RT-SKELETON-002 | handler 不 mutate 输入 state | 输入 RuntimeState 深拷贝相等 |
