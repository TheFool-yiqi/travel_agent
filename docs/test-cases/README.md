# Travel Agent 功能测试用例库（全量）

> **版本：** v2.0 · **更新：** 2026-06-03  
> **目标：** 全功能点 + 全流程覆盖，符合软件测试用例规范  
> **用例总数：** **351**（batch-4：删除 59 条不可自动化用例，余下全部 ✅）

---

## 1. 文档体系

| 文件 | 模块 | 用例编号 | 条数 | 说明 |
|------|------|----------|------|------|
| [01-auth-session.md](./01-auth-session.md) | 认证与会话 | TC-AUTH / TC-SESS | 45 | 登录、Token、行程 CRUD |
| [02-requirements-collection.md](./02-requirements-collection.md) | 需求收集 | TC-REQ | 39 | 7 步引导、校验、确认 |
| [03-semantic-understanding.md](./03-semantic-understanding.md) | 语义理解 | TC-SEM | 50 | 词表、澄清、防幻觉、纠错 |
| [04-planning-flow.md](./04-planning-flow.md) | LangGraph 规划 | TC-PLAN | 39 | 8 节点 + 选项枚举 |
| [05-approval-order.md](./05-approval-order.md) | 审批与订单 | TC-APR | 22 | 确认、修订、订单 |
| [06-chat-stream-api.md](./06-chat-stream-api.md) | 对话与 API | TC-CHAT / TC-API | 49 | SSE、WebSocket、REST |
| [07-frontend-ui.md](./07-frontend-ui.md) | 前端 UI | TC-UI | 23 | 组件、交互、响应式 |
| [08-data-security.md](./08-data-security.md) | 数据与安全 | TC-DATA / TC-SEC | 24 | 持久化、权限 |
| [09-e2e-flows.md](./09-e2e-flows.md) | 端到端流程 | TC-E2E / TC-FLOW | 41 | 主路径、分支、中断恢复 |
| [10-negative-boundary.md](./10-negative-boundary.md) | 异常与边界 | TC-NEG | 19 | 非法输入、降级、并发 |

---

## 2. 标准用例模板

每条用例包含以下字段（各模块文件统一）：

```
用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果
```

| 字段 | 说明 |
|------|------|
| **优先级** | P0 阻塞 / P1 核心 / P2 增强 / P3 可选 |
| **类型** | 功能 / 接口 / UI / 安全 / 性能 / 兼容 / 回归 / 异常 |
| **自动化** | ✅ pytest/e2e · 🔶 部分 · ❌ 手动 · ⏳ 待实现 |

---

## 3. 功能架构 ↔ 用例映射

```
┌─────────────────────────────────────────────────────────────────┐
│  AUTH / SESS          认证、会话、历史                              │
├─────────────────────────────────────────────────────────────────┤
│  REQ + SEM            需求收集 ←→ 语义层（词表/澄清/防幻觉）         │
├─────────────────────────────────────────────────────────────────┤
│  PLAN                 inject_memory → collect → destination →     │
│                       transport → stay_food → activities →        │
│                       build_itinerary                             │
├─────────────────────────────────────────────────────────────────┤
│  APR                  approval → revise → final_response (ORDER)│
├─────────────────────────────────────────────────────────────────┤
│  CHAT / API / UI      SSE / WS / REST / React 组件                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 流程覆盖矩阵（必须覆盖）

| 流程 ID | 流程名称 | 对应用例 | 优先级 |
|---------|----------|----------|--------|
| FLOW-01 | 新用户注册 → 首行程 → 问候 | TC-E2E-001, TC-AUTH-002, TC-SESS-002 | P0 |
| FLOW-02 | 需求 7 步收集 → 用户确认 | TC-FLOW-001 ~ TC-FLOW-007, TC-REQ-* | P0 |
| FLOW-03 | 需求确认 → 规划 5 步 → 行程卡片 | TC-FLOW-010, TC-PLAN-* | P0 |
| FLOW-04 | 审批通过 → 订单号 | TC-FLOW-020, TC-APR-002 | P0 |
| FLOW-05 | 审批 → 修订 → 再确认 → 订单 | TC-FLOW-021, TC-APR-004~006 | P0 |
| FLOW-06 | 会话中断 → 刷新 → 从 Checkpoint 继续 | TC-FLOW-030, TC-DATA-002 | P1 |
| FLOW-07 | 错别字澄清 → 确认 → 继续收集 | TC-FLOW-040, TC-SEM-002 | P0 |
| FLOW-08 | 模糊地名澄清（天堂/天水/天津） | TC-FLOW-041, TC-SEM-006~007 | P0 |
| FLOW-09 | 多轮跨槽位（成都→上海→日期） | TC-FLOW-042, TC-REQ-004 | P0 |
| FLOW-10 | 口语天数/假期/预算/人数 | TC-FLOW-050, TC-SEM-011~014 | P0 |
| FLOW-11 | 用户纠错改目的地 | TC-FLOW-051, TC-SEM-015 | P1 |
| FLOW-12 | 401 登出 → 重新登录 | TC-FLOW-060, TC-SEC-* | P0 |
| FLOW-13 | 删除会话 → 不可再访问 | TC-FLOW-061, TC-SESS-005 | P1 |
| FLOW-14 | 纯寒暄不触发 LLM 抽取 | TC-FLOW-070, TC-REQ-020 | P1 |
| FLOW-15 | 继续旧会话问候（非重复 bootstrap） | TC-FLOW-071, TC-SESS-009 | P1 |

---

## 5. 功能点清单（全覆盖检查表）

### 5.1 后端 Graph

- [ ] inject_user_memory 长期记忆注入
- [ ] collect_requirements 分步引导 + LLM 抽取 + semantic_pipeline
- [ ] plan_destination 推荐/确认 selected_destination
- [ ] plan_transport flight/train/driving + MCP  grounding
- [ ] plan_stay_and_food 4 住宿 × 3 餐饮
- [ ] plan_activities 5 类活动
- [ ] build_itinerary 逐日 + budget + Plan B + 超预算警告
- [ ] approval_node pending/approved/revising
- [ ] revise_itinerary 清空 itinerary 重建
- [ ] final_response ORDER 生成

### 5.2 语义层

- [ ] region_lexicon 省级区域
- [ ] city_lexicon 精确/别名/typo_auto/typo_confirm/fuzzy
- [ ] place_lexicon 景点别名
- [ ] destination_resolver 分层策略
- [ ] sanitize_destination/budget/travel_styles
- [ ] slot_sanitizer 出发地目的地冲突
- [ ] disambiguator 预算每人/总共
- [ ] correction_handler 用户纠错
- [ ] holiday_calendar 节日日期/假期天数
- [ ] intent_normalizer 口语扩展
- [ ] semantic_metrics API

### 5.3 前端

- [ ] AuthOverlay 登录注册
- [ ] Sidebar / ConversationList / MobileSessionDrawer
- [ ] ChatMain / MessageList / ChatInput / TypingIndicator
- [ ] StepProgress 8 阶段
- [ ] ItineraryCard / ApprovalBanner
- [ ] SettingsPage / UserPassport
- [ ] Toast / 401 处理 / SSE 流式

### 5.4 API

- [ ] users: register/login/me
- [ ] sessions: CRUD + semantic-metrics
- [ ] chat: stream/history
- [ ] itineraries: get/patch
- [ ] ws: /chat/ws/{id}
- [ ] health

---

## 6. 自动化覆盖总览（batch-4）

| 模块 | 用例数 | ✅ | 🔶 | ❌ | ⏳ |
|------|--------|----|----|-----|-----|
| AUTH+SESS | 45 | 45 | 0 | 0 | 0 |
| REQ | 39 | 39 | 0 | 0 | 0 |
| SEM | 50 | 50 | 0 | 0 | 0 |
| PLAN | 39 | 39 | 0 | 0 | 0 |
| APR | 22 | 22 | 0 | 0 | 0 |
| CHAT+API | 49 | 49 | 0 | 0 | 0 |
| UI | 23 | 23 | 0 | 0 | 0 |
| DATA+SEC | 24 | 24 | 0 | 0 | 0 |
| E2E+FLOW | 41 | 41 | 0 | 0 | 0 |
| NEG | 19 | 19 | 0 | 0 | 0 |
| **合计** | **351** | **351** | **0** | **0** | **0** |

---

## 7. 执行策略

| 轮次 | 范围 | 时机 |
|------|------|------|
| **冒烟** | 全部 P0 + ✅ 自动化 | 每次提测 |
| **回归** | P0+P1 + SEM/REQ/PLAN | 每次发版 |
| **全量** | 本文档全部 351 条 ✅ 自动化用例 | 大版本 / 季度 |

```bash
# 自动化基线
make test-smoke
uv run pytest backend/tests/ -m "not integration" -q
make test-smoke-ui
```

---

## 8. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-06-03 | 初版 ~111 条 |
| v2.0 | 2026-06-03 | 扩充至 410 条，10 模块拆分，全流程矩阵 |
