# V1 Streaming Frontend Adapter Implementation Plan

> **For agentic workers:** implement this plan task-by-task. Do not commit unless the
> user explicitly asks. This plan covers Slice 9 (roadmap Phase 8).

**Goal:** 将 `RuntimeEvent` 与 public token 流映射为现有 SSE/WS 前端契约
（`step`、`token`、`itinerary`、`approval_required`、`order`、`done`、`error`）。

**Architecture:** `frontend_adapter.adapt_runtime_event_to_frontend_events()` 负责单事件
映射；`runtime_chat_stream.iter_frontend_transport_events()` 复用 Slice 2 多路复用器并
输出前端 transport dict。不切换默认 chat 路径（Phase 9）。

**Prerequisites:** Slice 8 已完成（approval pause、finalize order、153 runtime 测试全绿）。

---

## 1. Scope

```text
RUNTIME_STAGE_LABELS for V1 stage progress display
adapt_runtime_event_to_frontend_events(RuntimeEvent) -> list[dict]
iter_frontend_transport_events(runtime_events, token_queue) -> AsyncIterator[dict]
itinerary / approval / order mapping from stage_completed outputs
public_reply -> token on collect / approve / finalize
Slice 9 adapter unit tests + multiplex integration test + smoke test
更新 runtime-framework-inventory.md 与 README.md
```

### Out Of Scope

```text
切换 chat_stream 默认路径到 PlanningRuntime
WebSocket handler wiring
message persistence / extra_info merge
LangGraph checkpoint interrupt/resume transport
frontend UI changes
```

## 2. Event Mapping

| RuntimeEvent | Frontend events |
|--------------|-----------------|
| `stage_started` | `step` |
| `stage_completed` (integrate) | `itinerary` |
| `stage_completed` (approve waiting) | `approval_required` + optional `token` |
| `stage_completed` (finalize) | `order` + optional `token` |
| `stage_completed` (any with public_reply) | `token` |
| `runtime_completed` | `done` |
| `runtime_failed` | `error` |
| token queue item | `token` |

## 3. Completion Criteria

```text
RuntimeEvent maps to existing transport event types
parallel stage tokens do not bypass single public token queue policy
approval_required emitted when approve_or_revise returns waiting
integrate emits itinerary card payload
finalize emits order_id
full runtime smoke yields step + itinerary + approval_required or done
Slice 1-8 tests still pass
```

Next: Phase 9 old flow retirement (default chat path switch).
