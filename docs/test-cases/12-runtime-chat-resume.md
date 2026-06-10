# Runtime 流式、会话与 Resume 测试用例

> **编号：** TC-RT-STREAM-* · TC-RT-SESS-* · TC-RT-RESUME-*  
> **执行：** `uv run python scripts/run_test_case.py TC-RT-STREAM-001`

---

## 1. Chat 路径与 SSE（TC-RT-STREAM）

| 编号 | 名称 | 优先级 | 步骤 | 成功指标 |
|------|------|--------|------|----------|
| TC-RT-STREAM-001 | chat 仅走 Runtime | P0 | 调用 `iter_chat_events` | monkeypatch 证明调用 `iter_chat_events_runtime` |
| TC-RT-STREAM-002 | stage_started→step | P0 | adapt 单事件 | SSE JSON `type=step`；`step` 为 Runtime 阶段 label |
| TC-RT-STREAM-003 | integrate→itinerary | P0 | adapt integrate 完成事件 | SSE `type=itinerary`；含 days/budget |
| TC-RT-STREAM-004 | approve→approval_required | P0 | adapt waiting 事件 | SSE `type=approval_required` + token 提示 |
| TC-RT-STREAM-005 | finalize→ORDER token | P0 | adapt finalize | SSE token 含 `ORDER-` |
| TC-RT-STREAM-006 | runtime_completed→done | P0 | adapt 完成 | SSE `type=done` |
| TC-RT-STREAM-007 | runtime_failed→error | P1 | inject 失败 | SSE `type=error` |
| TC-RT-STREAM-008 | 内部事件不泄露 | P2 | visibility=internal | 前端流中不可见 |
| TC-RT-STREAM-009 | token 流式 drain | P1 | iter_runtime_events_and_tokens | collect 期间 token 不丢失 |
| TC-RT-STREAM-010 | SSE 格式 data: 前缀 | P1 | `test_sse_format` | 每行 `data: {...}\n\n` |

### SSE 事件契约检查表

| 事件 type | 触发阶段 | 必填字段 | 前端消费组件 |
|-----------|----------|----------|--------------|
| `step` | 任意 stage_started | `step`, `label?` | StepProgress |
| `token` | LLM 流式 | `content` | MessageList |
| `itinerary` | integrate 完成 | `itinerary`, `budget` | ItineraryCard |
| `approval_required` | approve_or_revise 等待 | `itinerary` | ApprovalBanner |
| `error` | runtime_failed | `message` | Toast |
| `done` | runtime_completed | — | 解锁输入框 |

---

## 2. 会话持久化（TC-RT-SESS）

| 编号 | 名称 | 优先级 | 步骤 | 成功指标 |
|------|------|--------|------|----------|
| TC-RT-SESS-001 | finalize 后 reset turn | P0 | 模拟 completed finalize | 下轮 `should_reset_runtime_turn=true` |
| TC-RT-SESS-002 | awaiting_user 不 reset | P0 | collect 等待中 | `should_reset=false`；state 保留 |
| TC-RT-SESS-003 | extra_info 恢复 state | P0 | 写入 planning_runtime | load 后 stage/status 一致 |
| TC-RT-SESS-004 | 追加 user public message | P1 | prepare_runtime_turn | messages 末尾为 HumanMessage |
| TC-RT-SESS-005 | F5 刷新后继续 | P0 | E2E TC-FLOW-030 | 历史消息仍在；可继续输入 |
| TC-RT-SESS-006 | 旧会话不重复问候 | P1 | E2E TC-FLOW-071 | 无第二条 bootstrap 问候 |

**持久化字段检查**

```text
travel_sessions.extra_info.planning_runtime
  ├── run_id
  ├── current_stage
  ├── stage_status          # running | waiting | completed | failed
  ├── collect_context
  ├── planning_need
  ├── itinerary_draft
  └── approval_status
```

---

## 3. Resume（TC-RT-RESUME）

| 编号 | 名称 | 优先级 | 场景 | 成功指标 |
|------|------|--------|------|----------|
| TC-RT-RESUME-001 | collect 多轮 resume | P0 | 首轮 waiting → 下轮补槽 | 第二轮仍从 collect 开始；不跳过确认 |
| TC-RT-RESUME-002 | approve 等待 resume | P0 | 出 itinerary 后暂停 → 用户「确认」 | 从 approve_or_revise 继续 → finalize |
| TC-RT-RESUME-003 | 修订 resume | P0 | 用户「修改」→ 再确认 | verify 重跑；二次 approval_required |
| TC-RT-RESUME-004 | 跨会话 thread 绑定 | P1 | 指定 thread_id | checkpoint/state 与 session 一致 |

---

## 4. API 层（关联 TC-CHAT）

| 编号 | 名称 | 成功指标 |
|------|------|----------|
| TC-CHAT-001 | stream 需 JWT | 无 Authorization → 401 |
| TC-CHAT-003 | SSE 含 step | 响应体含 `"type":"step"` |
| TC-CHAT-004 | 持久化入口 | `generate_sse_stream` 被调用 |
| TC-CHAT-007 | 跨用户 stream | error 或 404 语义 |
| TC-CHAT-018 | 异常降级 | SSE error 事件 |

---

## 5. 执行示例

```bash
# 流式契约全套（pytest）
uv run python scripts/run_test_case.py TC-RT-STREAM-001
uv run python scripts/run_test_case.py TC-RT-STREAM-002
uv run python scripts/run_test_case.py TC-RT-STREAM-003
uv run python scripts/run_test_case.py TC-RT-STREAM-004

# 会话 + resume
uv run python scripts/run_test_case.py --suite SUITE-RUNTIME --layer pytest | head
```
