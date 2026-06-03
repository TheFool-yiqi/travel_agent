# 端到端流程测试用例

> **模块：** E2E / FLOW · **用例数：** 45 · **版本：** v2.0 · **更新：** 2026-06-03

覆盖主路径、分支路径及 README 流程矩阵 FLOW-01 ~ FLOW-15。

---

## TC-E2E 端到端场景（001–015）

| 用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 |
|----------|----------|--------|------|--------|----------|----------|----------|----------|
| TC-E2E-001 | 新用户注册→首行程→问候 | P0 | E2E | ✅ | 全栈 | 1. 注册 2. 规划新行程 | e2e 用户 | 问候语；session 创建 |
| TC-E2E-002 | 主路径登录到订单 | P0 | E2E | ✅ | 已注册 | 1. main-path 全流程 | smoke 主路径 | ORDER- 订单号 |
| TC-E2E-003 | 修订路径 E2E | P0 | E2E | ⏳ | 至 approval | 1. revision-path | 修改第三天 | 新行程+二次订单 |
| TC-E2E-004 | 异常路径 E2E 穿插 | P1 | E2E | ⏳ | 收集中 | 1. exception-path | 程度/穷游 | 语义符合 exception doc |
| TC-E2E-005 | Playwright 鉴权壳层 | P0 | E2E | ✅ | frontend | 1. auth.spec | — | 浮层+注册通过 |
| TC-E2E-006 | pytest smoke 三路径全绿 | P0 | 回归 | ✅ | backend | 1. pytest -m smoke | — | main+revision+exception 绿 |
| TC-E2E-007 | make test-smoke 一键 | P0 | 回归 | ✅ | docker-up | 1. make test-smoke | — | 命令成功 |
| TC-E2E-008 | make test-smoke-ui | P1 | E2E | ⏳ | dev servers | 1. make test-smoke-ui | — | pytest+playwright |
| TC-E2E-009 | 后端无 LLM 冒烟 | P0 | 回归 | ✅ | mock/路由 | 1. smoke 单元 | — | 不依赖真实 LLM |
| TC-E2E-010 | 手动主路径 Checklist | P1 | E2E | ❌ | 人工 | 1. main-path.md 勾选 | — | 8 阶段+订单 |
| TC-E2E-011 | 手动修订 Checklist | P1 | E2E | ❌ | 人工 | 1. revision-path.md | — | 修订+订单 |
| TC-E2E-012 | 手动异常 Checklist | P1 | E2E | ❌ | 人工 | 1. exception-path E1~E8 | — | 全符合 |
| TC-E2E-013 | 发布前全量 UI 走查 | P2 | E2E | ❌ | 发版前 | 1. README 执行策略 | — | P0+P1 通过 |
| TC-E2E-014 | 跨浏览器 Chrome/Firefox | P2 | 兼容 | ❌ | playwright 多项目 | 1. 跑 e2e | — | 核心用例绿 |
| TC-E2E-015 | 后端-only CI 流水线 | P1 | 回归 | ✅ | CI | 1. pytest not integration | — | 稳定绿 |

---

## TC-FLOW 业务流程（001–030）

| 用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 |
|----------|----------|--------|------|--------|----------|----------|----------|----------|
| TC-FLOW-001 | FLOW-02 步1 目的地 | P0 | 流程 | ✅ | 新会话 | 1. 输入目的地 | `北京` | 追问出发城市 |
| TC-FLOW-002 | FLOW-02 步2 出发城市 | P0 | 流程 | ✅ | 步1 完成 | 1. `上海` | — | 追问日期 |
| TC-FLOW-003 | FLOW-02 步3 出发日期 | P0 | 流程 | ✅ | 步2 完成 | 1. `2026-06-19` | 端午 | 追问天数 |
| TC-FLOW-004 | FLOW-02 步4 天数 | P0 | 流程 | ✅ | 步3 完成 | 1. `3天` | — | 追问人数 |
| TC-FLOW-005 | FLOW-02 步5 人数 | P0 | 流程 | ✅ | 步4 完成 | 1. `就我一个人` | — | 追问预算 |
| TC-FLOW-006 | FLOW-02 步6 预算 | P0 | 流程 | ✅ | 步5 完成 | 1. `穷游党` | — | 需求摘要 |
| TC-FLOW-007 | FLOW-02 步7 确认 | P0 | 流程 | ✅ | 摘要展示 | 1. `对的` | — | → plan_destination |
| TC-FLOW-010 | FLOW-03 规划至行程卡片 | P0 | 流程 | ⏳ | 需求已确认 | 1. 目的地→交通→食宿→活动→build | smoke | ItineraryCard+approval |
| TC-FLOW-020 | FLOW-04 审批通过订单 | P0 | 流程 | ⏳ | approval pending | 1. 确认行程 | — | ORDER 生成 |
| TC-FLOW-021 | FLOW-05 修订再确认订单 | P0 | 流程 | ⏳ | 有 itinerary | 1. 修改 2. 确认 | 修订意见 | 新 ORDER |
| TC-FLOW-030 | FLOW-06 中断刷新恢复 | P1 | 流程 | ⏳ | 收集中途 | 1. 填部分槽 2. F5 3. 继续 | — | checkpoint 恢复 |
| TC-FLOW-040 | FLOW-07 错别字澄清链 | P0 | 流程 | ✅ | 新会话 | 1. `程度` 2. `对` 3. `上海` | E1 | 成都+上海 |
| TC-FLOW-041 | FLOW-08 天堂澄清 | P0 | 流程 | ✅ | destination 步 | 1. `天堂` | — | clarify；不绑天津 |
| TC-FLOW-042 | FLOW-09 多轮跨槽 | P0 | 流程 | ⏳ | 新会话 | 1. `成都` 2. `上海` 3. 日期 | — | 三槽正确 |
| TC-FLOW-050 | FLOW-10 口语天数假期预算 | P0 | 流程 | ✅ | 日期已填 | 1. `整个假期` 2. 穷游党 | — | days=3；预算后填 |
| TC-FLOW-051 | FLOW-11 纠错改目的地 | P1 | 流程 | ✅ | dest=北京 | 1. `改成杭州` | — | destination=杭州 |
| TC-FLOW-060 | FLOW-12 401 重登 | P0 | 流程 | ⏳ | 已登录 | 1. 废 token 2. 调 API | — | AuthOverlay；重登成功 |
| TC-FLOW-061 | FLOW-13 删会话不可访问 | P1 | 流程 | ✅ | 有会话 | 1. DELETE 2. GET/stream | — | 404 |
| TC-FLOW-070 | FLOW-14 寒暄不抽取 | P1 | 流程 | ✅ | 收集中 | 1. `你好` | — | 无虚假槽 |
| TC-FLOW-071 | FLOW-15 旧会话不重复问候 | P1 | 流程 | ⏳ | 旧 session | 1. 打开 2. 发消息 | — | 无第二条 bootstrap |
| TC-FLOW-008 | 交通确认高铁 | P0 | 流程 | ⏳ | plan_transport | 1. `高铁` | — | → 食宿 |
| TC-FLOW-009 | 食宿+活动 shorthand | P0 | 流程 | ⏳ | stay/activity | 1. 经济酒店+本地小吃 2. 文化 | smoke | → build |
| TC-FLOW-011 | 目的地确认「就北京」 | P1 | 流程 | ⏳ | plan_destination | 1. `就北京` | — | selected_destination |
| TC-FLOW-012 | 超预算警告可见 | P1 | 流程 | ⏳ | 低预算 | 1. build | 穷游 | 警告文案 |
| TC-FLOW-013 | 订单含关键字段 | P0 | 流程 | ⏳ | final | 1. 读回复 | — | ORDER+目的地+预算 |
| TC-FLOW-014 | 进度条与 graph 同步 | P1 | UI | ⏳ | 全流程 | 1. 每步查 StepProgress | — | 8 步一致 |
| TC-FLOW-015 | 双用户并行会话隔离 | P1 | 安全 | ❌ | 两浏览器 | 1. 各建会话 | — | 互不可见 |
| TC-FLOW-016 | 同用户多会话独立 state | P1 | 功能 | ⏳ | 2 sessions | 1. 不同目的地 | 北京/成都 | checkpoint 隔离 |
| TC-FLOW-017 | 从 approval 确认英文 OK | P2 | 流程 | ✅ | pending | 1. `OK` | — | → final |
| TC-FLOW-018 | 从 approval 修改英文 | P2 | 流程 | ✅ | pending | 1. `change hotel` | — | → revise |
| TC-FLOW-019 | collect 未完成不进 plan | P0 | 流程 | ✅ | 缺 budget | 1. 试图跳过 | — | 停留 collect |
| TC-FLOW-022 | semantic-metrics 随 FLOW 增长 | P2 | 功能 | ⏳ | 走完 collect | 1. GET metrics | — | 命中率有值 |
| TC-FLOW-023 | 完整 FLOW 文档对照 | P1 | 回归 | ❌ | — | 1. README 矩阵 15 条 | — | 均有对应用例 |

### TC-FLOW-042 扩展说明（FLOW-09 · 多轮跨槽）

| 轮次 | 用户输入 | 预期 state |
|------|----------|------------|
| 1 | `成都` | destination=成都；问出发城市 |
| 2 | `上海` | departure_city=上海；destination 仍为成都 |
| 3 | `2026-07-01` | departure_date 写入；问 travel_days |

- **缺口：** smoke 自动化 ⏳；`test_smoke_flows` 仅测 guidance 保留 destination
- **建议 e2e：** 扩展 `exception-path.spec.ts` 或新建 `multi-slot.spec.ts`

---

## 流程矩阵对照

| 流程 ID | 对应用例 |
|---------|----------|
| FLOW-01 | TC-E2E-001, TC-FLOW-001 |
| FLOW-02 | TC-FLOW-001 ~ 007 |
| FLOW-03 | TC-FLOW-010, TC-FLOW-008~009 |
| FLOW-04 | TC-FLOW-020 |
| FLOW-05 | TC-FLOW-021 |
| FLOW-06 | TC-FLOW-030 |
| FLOW-07 | TC-FLOW-040 |
| FLOW-08 | TC-FLOW-041 |
| FLOW-09 | TC-FLOW-042 |
| FLOW-10 | TC-FLOW-050 |
| FLOW-11 | TC-FLOW-051 |
| FLOW-12 | TC-FLOW-060 |
| FLOW-13 | TC-FLOW-061 |
| FLOW-14 | TC-FLOW-070 |
| FLOW-15 | TC-FLOW-071 |

---

## 自动化映射

| 测试文件 | 覆盖用例 |
|----------|----------|
| `test_smoke_flows.py` | TC-E2E-006, TC-FLOW-001~007, 040~041, 050~051, 017~019 |
| `e2e/main-path.spec.ts` | TC-E2E-002, TC-FLOW-010（部分） |
| `e2e/auth.spec.ts` | TC-E2E-005 |
| `e2e/revision-path.spec.ts` | TC-E2E-003 |
| `e2e/exception-path.spec.ts` | TC-E2E-004 |
