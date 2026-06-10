# V1 User Revision Routing Implementation Plan

> **For agentic workers:** implement this plan task-by-task. Do not commit unless the
> user explicitly asks.

**Goal:** 用户提出修改意见后，`approve_or_revise` 应用 deterministic 修订、重新验证，
并再次发出 `approval_required` + 更新后的 `itinerary` 事件。

**Prerequisites:** Phase 9 已完成（默认 chat 走 PlanningRuntime）。

---

## 1. Scope

```text
RevisionAgent.revise_from_user_feedback()
approve_or_revise 修订分支 + 重新 QualityVerifier
frontend adapter 在 approve waiting 时 emit itinerary
E2E helpers 对齐 Runtime 自动规划路径
```

## 2. Completion Criteria

```text
用户修改消息后 revision_count +1 且 itinerary_draft 更新
前端可再次看到 approval banner
runtime + adapter tests pass
```
