# V1 Old Flow Retirement Implementation Plan

> **For agentic workers:** implement this plan task-by-task. Do not commit unless the
> user explicitly asks. This plan covers Phase 9 / Slice 10.

**Goal:** 将 SSE/WS chat 默认路径切换为 PlanningRuntime，同时保留旧 LangGraph 兼容入口。

**Architecture:** `iter_chat_events` 按 `CHAT_PLANNER_BACKEND` 分发；
`runtime_chat_service.iter_chat_events_runtime` 负责会话持久化、resume 与前端 transport；
`travel_sessions.extra_info.planning_runtime` 保存跨轮 RuntimeState。

**Prerequisites:** Slice 9 已完成（frontend adapter merged）。

---

## 1. Scope

```text
CHAT_PLANNER_BACKEND=runtime|graph（默认 runtime）
session_state 持久化 / resume / reset
PlanningRuntime resume from current_stage when awaiting_user
build_production_stage_handlers + ServiceItineraryPersistenceAdapter
iter_chat_events_runtime wired as default chat path
保留 iter_chat_events_graph 兼容入口
docs/architecture.md + inventory 更新
```

### Out Of Scope

```text
删除旧 graph 文件
LangGraph checkpoint 与 Runtime 状态双写
frontend UI 改造
RevisionAgent 完整修订路由
```

## 2. Completion Criteria

```text
iter_chat_events 默认走 PlanningRuntime
CHAT_PLANNER_BACKEND=graph 可回退旧路径
collect / approval 多轮 resume 通过 session extra_info
finalize 走 ServiceItineraryPersistenceAdapter
core runtime + chat dispatch tests pass
```
