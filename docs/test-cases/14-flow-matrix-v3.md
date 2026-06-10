# 业务流程矩阵 v3（PlanningRuntime）

> **版本：** v3.0 · **替代：** README §4 中基于 LangGraph 节点的 FLOW 描述  
> **E2E 执行：** `uv run python scripts/run_test_case.py --suite SUITE-E2E-P0`

---

## 1. 主路径（P0）

| Flow ID | 名称 | 用户操作序列 | 预期阶段轨迹 | 成功指标 | 用例 |
|---------|------|--------------|--------------|----------|------|
| **FLOW-RT-01** | 注册首会话 | 注册 → 规划新行程 | bootstrap 问候 | 助手含「目的地/旅行」；输入框可用 | TC-E2E-001 |
| **FLOW-RT-02** | 需求七步收集 | 北京→上海→日期→3天→1人→穷游→对的 | collect（多轮 waiting） | 出现需求摘要/确认提示 | TC-E2E-002 前半 |
| **FLOW-RT-03** | 自动规划至审批 | 确认「对的」后无需选手动步骤 | collect → … → approve_or_revise | `行程确认` region 可见；ItineraryCard | TC-E2E-002 |
| **FLOW-RT-04** | 确认出单 | 点击「确认行程」 | approve_or_revise → finalize | 助手消息匹配 `ORDER-[A-F0-9]{8,}` | TC-E2E-002 / FLOW-020 |
| **FLOW-RT-05** | 修订再确认 | 输入「修改」→ 调整 → 再确认 | approve → verify → approve → finalize | 两条 ORDER 前仅一条；或修订后新 itinerary | TC-E2E-003 |

### FLOW-RT-03 阶段期望（自动，无用户逐步选择）

```text
prepare_base_context → retrieve_evidence → tool_enrich → domain_plan
→ integrate → verify → approve_or_revise (waiting)
```

---

## 2. 语义与澄清（P0）

| Flow ID | 名称 | 输入 | 成功指标 | 用例 |
|---------|------|------|----------|------|
| **FLOW-RT-10** | 程度→成都 | 「程度」 | clarify 成都；不写入错误 destination | TC-FLOW-040 / TC-SEM-002 |
| **FLOW-RT-11** | 天堂模糊 | 「天堂」 | 不自动绑定天津/天水 | TC-FLOW-041 / TC-SEM-006 |
| **FLOW-RT-12** | 跨槽位多轮 | 成都→改上海→日期 | destination 最终为上海 | TC-FLOW-042 / TC-REQ-004 |
| **FLOW-RT-13** | 用户纠错 | 「改成杭州」 | detect_user_correction 命中 | TC-FLOW-051 / TC-SEM-015 |
| **FLOW-RT-14** | 纯寒暄 | 「你好」 | 不进入 domain_plan | TC-FLOW-070 / TC-RT-COLLECT-001 |

---

## 3. 会话与认证（P0–P1）

| Flow ID | 名称 | 成功指标 | 用例 |
|---------|------|----------|------|
| **FLOW-RT-20** | F5 刷新续聊 | 刷新后消息保留、可发送 | TC-FLOW-030 |
| **FLOW-RT-21** | 旧会话打开 | 无重复 bootstrap | TC-FLOW-071 |
| **FLOW-RT-22** | 无效 token | AuthOverlay 再现 | TC-FLOW-060 |
| **FLOW-RT-23** | 删会话 | history/stream 404 | TC-FLOW-061 / TC-SESS-005 |

---

## 4. 异常与边界（P1）

| Flow ID | 名称 | 成功指标 | 用例 |
|---------|------|----------|------|
| **FLOW-RT-30** | 过去日期 | 校验拒绝 | TC-NEG-001 |
| **FLOW-RT-31** | 空消息 | stream 422 | test_empty_message_stream_422 |
| **FLOW-RT-32** | XSS 城市名 | 不 accept 为 city | TC-NEG-020 |
| **FLOW-RT-33** | 非法 food enum | 规则抽取过滤 | TC-NEG-006 |
| **FLOW-RT-34** | Runtime 阶段失败 | SSE error + 输入恢复 | TC-CHAT-018 |

---

## 5. 套件门禁

| 门禁 | 包含 Flow | PASS 条件 |
|------|-----------|-----------|
| **发版 P0** | FLOW-RT-01~05, 10~12, 20, 22 | SUITE-E2E-P0 + SUITE-SMOKE 全 PASS |
| **日常 CI** | FLOW-RT-01~04（pytest 层） | SUITE-RUNTIME + SUITE-API PASS |
| **季度全量** | 全部 FLOW-RT-* | TC-SUITE-FULL-BACKEND ≥700 passed + E2E 全量 |

---

## 6. AI 执行顺序（推荐）

```text
1. SUITE-SMOKE          (~10 cases, <3 min)
2. SUITE-RUNTIME        (~37 cases, <5 min)
3. SUITE-SEM-REQ        (~8 cases)
4. SUITE-API            (~10 cases)
5. SUITE-E2E-P0         (需 :8200, ~30–60 min)
6. TC-SUITE-FULL-BACKEND
```

```bash
uv run python scripts/run_test_case.py --suite SUITE-SMOKE --log
uv run python scripts/run_test_case.py --suite SUITE-RUNTIME --log
uv run python scripts/run_test_case.py --suite SUITE-E2E-P0 --log
```
