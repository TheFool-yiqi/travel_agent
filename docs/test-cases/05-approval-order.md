# 审批与订单测试用例

> **模块：** APR · **用例数：** 22 · **版本：** v2.0 · **更新：** 2026-06-03

覆盖 `approval_node`、`revise_itinerary`、`final_response`、`approval_router` 及前端 `ApprovalBanner`。

**状态机：** pending → approved / revising → build_itinerary → pending → final_response

---

| 用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 |
|----------|----------|--------|------|--------|----------|----------|----------|----------|
| TC-APR-001 | build 完成后进入 approval pending | P0 | 功能 | ✅ | itinerary 已生成 | 1. route_after_itinerary | — | current=approval_node；approval_status=pending |
| TC-APR-002 | 用户确认关键词识别 | P0 | 功能 | ✅ | pending | 1. user_wants_approval | `确认行程`/`OK` | 返回 true |
| TC-APR-003 | 确认后路由 final_response | P0 | 功能 | ✅ | 用户确认 | 1. route_after_approval | current=final_response | next=final_response |
| TC-APR-004 | 生成 ORDER 订单号 | P0 | 功能 | ✅ | 进入 final_response | 1. 读助手回复 | — | 含 `ORDER-` + 8 位以上字符 |
| TC-APR-005 | 订单含目的地与预算摘要 | P0 | 功能 | ✅ | 订单生成 | 1. 检查回复 | — | 目的地、预算与 state 一致 |
| TC-APR-006 | 修订关键词识别 | P0 | 功能 | ✅ | pending | 1. user_wants_revision | `修改第二天`/`change hotel` | 返回 true |
| TC-APR-007 | 修订路由 revise_itinerary | P0 | 功能 | ✅ | 用户要改 | 1. route_after_approval | revising | next=revise_itinerary |
| TC-APR-008 | revise 清空 itinerary 重建 | P0 | 功能 | ✅ | 进入 revise | 1. 查 state | — | itinerary 清空后 rebuild |
| TC-APR-009 | 修订后回到 approval pending | P0 | 功能 | ✅ | rebuild 完成 | 1. 查 approval_status | — | 再次 pending；新卡片 |
| TC-APR-010 | 二次确认可出订单 | P0 | 功能 | ✅ | 修订后 | 1. 再点确认 | — | ORDER 生成；不重复旧单逻辑错误 |
| TC-APR-011 | 非确认非修订继续等待 | P1 | 功能 | ✅ | pending | 1. `再看看` | 模糊 | 停留 approval；友好回复 |
| TC-APR-012 | ApprovalBanner 显示 | P0 | UI | ✅ | itinerary 可见 | 1. 查 DOM | — | 文案「行程已生成，请确认或提出修改」 |
| TC-APR-013 | Banner「确认行程」按钮 | P0 | UI | ✅ | Banner 可见 | 1. 点击确认 | — | 发送确认意图；progress→完成 |
| TC-APR-014 | Banner「请求修改」按钮 | P0 | UI | ✅ | Banner 可见 | 1. 点击修改 | — | 进入修订流 |
| TC-APR-015 | 对话式确认与按钮等价 | P1 | UI | ✅ | Banner 可见 | 1. 输入 `确认` 代替点击 | — | 与按钮同效 |
| TC-APR-016 | 修订流式「正在重新生成」 | P1 | UI | ✅ | 提交修改 | 1. 观察消息 | 修改意见 | 助手提示重新生成 |
| TC-APR-017 | 无 itinerary 不可 approval | P0 | 异常 | ✅ | itinerary 空 | 1. assert_step_requirements | — | approval 缺字段 |
| TC-APR-018 | 无 budget 不可 approval | P1 | 异常 | ✅ | budget 空 | 1. 同上 | — | missing budget |
| TC-APR-019 | 确认与修订互斥判定 | P1 | 功能 | ✅ | — | 1. 同句「确认但改酒店」 | — | revision 优先或 clarify |
| TC-APR-020 | 修订路径 smoke 自动化 | P0 | 回归 | ✅ | — | 1. pytest smoke_revision | — | keywords + route 全绿 |
| TC-APR-021 | 无限等待确认循环防护 | P1 | 异常 | ✅ | 已给明确修改 | 1. 连续模糊回复 | — | 不 infinite「仍在等待」 |
| TC-APR-022 | patch itinerary API 与修订 | P2 | 接口 | ✅ | 有 itinerary | 1. PATCH `/itineraries/{id}` | 局部字段 | 200；与 graph 修订不冲突 |

### TC-APR-004~010 扩展说明（修订路径 · FLOW-05）

```
build_itinerary → approval (pending)
  → 用户修改 → revise_itinerary → build_itinerary → approval (pending)
  → 用户确认 → final_response (ORDER-XXXXXXXX)
```

- **冒烟文档：** `docs/smoke-test/revision-path.md`
- **E2E：** `e2e/revision-path.spec.ts`（⏳）

---

## 自动化映射

| 测试文件 | 覆盖用例 |
|----------|----------|
| `test_smoke_flows.py` (smoke_revision) | TC-APR-002~003, 006~007, 020 |
| `test_approval_router.py` | TC-APR-002~003, 006~007, 019 |
| `test_itineraries_api.py` | TC-APR-022 |

## 流程关联

- FLOW-04：TC-APR-002~005
- FLOW-05：TC-APR-006~010
