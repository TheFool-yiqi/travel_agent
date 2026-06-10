# V1 Approval And Finalize Implementation Plan

> **For agentic workers:** implement this plan task-by-task. Do not commit unless the
> user explicitly asks. This plan covers Slice 8 (roadmap Phase 7).

**Goal:** 实现 `approve_or_revise` 审批暂停语义与 `finalize` 订单/最终消息产出，
复用现有 `itinerary_service` 持久化能力（测试可注入 stub）。

**Architecture:** `ApproveOrReviseStageHandler` 在首次到达时返回 `waiting` 并写入
`pending_approval`；用户确认后 `completed`。`FinalizeStageHandler` 调用
`OrderService` + `FinalResponseGenerator` + `ItineraryPersistenceAdapter`。

**Prerequisites:** Slice 7 已完成（`itinerary_draft` + `quality_report`）。

---

## 1. Scope

```text
PendingApproval / FinalizationResult schemas
OrderService.generate_order_id()
FinalResponseGenerator (no new facts beyond itinerary_draft)
ItineraryPersistenceAdapter (wraps itinerary_service; stub for tests)
approve_or_revise real handler (waiting + approval detection)
finalize real handler
RuntimeState approval_status / order_id / finalization_result
Slice 8 smoke test (approval waiting + approve resume + finalize)
```

### Out Of Scope

```text
LangGraph interrupt/resume wiring
frontend RuntimeEvent switch
full RevisionAgent routing on modify_with_feedback
Runtime as default chat path
```

## 2. Completion Criteria

```text
approve_or_revise pauses runtime with pending_approval
user 确认 resumes to approved and finalize completes
order_id generated exactly once
final message only cites itinerary_draft fields
persistence adapter callable with injectable stub in tests
```

Next: `18-v1-streaming-frontend-adapter-implementation-plan.md`
