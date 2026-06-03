# Travel Agent 功能测试用例库（全量）

> **版本：** v2.0 · **更新：** 2026-06-03  
> **目标：** 全功能点 + 全流程覆盖，符合软件测试用例规范  
> **用例总数：** **410**（见各模块文件）

---

## 1. 文档体系

| 文件 | 模块 | 用例编号 | 条数 | 说明 |
|------|------|----------|------|------|
| [01-auth-session.md](./01-auth-session.md) | 认证与会话 | TC-AUTH / TC-SESS | 45 | 登录、Token、行程 CRUD |
| [02-requirements-collection.md](./02-requirements-collection.md) | 需求收集 | TC-REQ | 45 | 7 步引导、校验、确认 |
| [03-semantic-understanding.md](./03-semantic-understanding.md) | 语义理解 | TC-SEM | 55 | 词表、澄清、防幻觉、纠错 |
| [04-planning-flow.md](./04-planning-flow.md) | LangGraph 规划 | TC-PLAN | 50 | 8 节点 + 选项枚举 |
| [05-approval-order.md](./05-approval-order.md) | 审批与订单 | TC-APR | 22 | 确认、修订、订单 |
| [06-chat-stream-api.md](./06-chat-stream-api.md) | 对话与 API | TC-CHAT / TC-API | 55 | SSE、WebSocket、REST |
| [07-frontend-ui.md](./07-frontend-ui.md) | 前端 UI | TC-UI | 35 | 组件、交互、响应式 |
| [08-data-security.md](./08-data-security.md) | 数据与安全 | TC-DATA / TC-SEC | 30 | 持久化、权限 |
| [09-e2e-flows.md](./09-e2e-flows.md) | 端到端流程 | TC-E2E / TC-FLOW | 48 | 主路径、分支、中断恢复 |
| [10-negative-boundary.md](./10-negative-boundary.md) | 异常与边界 | TC-NEG | 25 | 非法输入、降级、并发 |

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

## 6. 自动化覆盖总览（v2.0 目标）

| 模块 | 用例数 | ✅ | 🔶 | ❌ | ⏳ |
|------|--------|----|----|-----|-----|
| AUTH+SESS | 45 | 12 | 2 | 8 | 23 |
| REQ | 45 | 18 | 5 | 4 | 18 |
| SEM | 55 | 35 | 4 | 7 | 9 |
| PLAN | 50 | 15 | 8 | 4 | 23 |
| APR | 22 | 8 | 3 | 5 | 6 |
| CHAT+API | 55 | 22 | 3 | 16 | 14 |
| UI | 35 | 3 | 4 | 22 | 6 |
| DATA+SEC | 30 | 15 | 2 | 8 | 5 |
| E2E+FLOW | 48 | 2 | 5 | 7 | 34 |
| NEG | 25 | 10 | 3 | 17 | 0 |
| **合计** | **410** | **~140** | **~39** | **~98** | **~128** |

---

## 7. 执行策略

| 轮次 | 范围 | 时机 |
|------|------|------|
| **冒烟** | 全部 P0 + ✅ 自动化 | 每次提测 |
| **回归** | P0+P1 + SEM/REQ/PLAN | 每次发版 |
| **全量** | 本文档全部用例 | 大版本 / 季度 |
| **探索** | ⏳ 待自动化 P1 | 迭代补充 |

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
