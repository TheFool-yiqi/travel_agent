# 前端 UI 测试用例

> **模块：** UI · **用例数：** 23 · **版本：** v2.0 · **更新：** 2026-06-03

覆盖 `frontend/src/components/` 与 `pages/` 主要 React 组件及响应式交互。

---

| 用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 |
|----------|----------|--------|------|--------|----------|----------|----------|----------|
| TC-UI-001 | AuthOverlay 未登录强制展示 | P0 | UI | ✅ | 未登录 | 1. 打开 `/` | — | 浮层可见；不可绕过 |
| TC-UI-002 | AuthOverlay 登录 Tab | P0 | UI | ✅ | 浮层打开 | 1. 默认登录 Tab | — | 用户名/密码表单 |
| TC-UI-003 | AuthOverlay 注册 Tab 切换 | P1 | UI | ✅ | 浮层打开 | 1. 切注册 Tab | — | 含 email 字段 |
| TC-UI-004 | 注册成功关闭浮层 | P0 | UI | ✅ | backend 可达 | 1. 完成注册 | e2e 随机用户 | 进入 AppShell |
| TC-UI-005 | Sidebar「我的行程」标题 | P1 | UI | ✅ | 已登录 | 1. 查看 Sidebar | — | 文案可见 |
| TC-UI-006 | Sidebar「规划新行程」按钮 | P0 | UI | ✅ | 已登录 | 1. 点击按钮 | — | 新建会话并选中 |
| TC-UI-007 | ConversationList 会话条目 | P1 | UI | ✅ | 多会话 | 1. 查看列表 | — | 标题+时间；当前高亮 |
| TC-UI-008 | 切换会话更新 ChatMain | P0 | UI | ✅ | ≥2 会话 | 1. 点击另一会话 | — | 消息与进度切换 |
| TC-UI-009 | MobileSessionDrawer 窄屏 | P1 | UI | ✅ | viewport 375px | 1. 打开 drawer | — | 会话列表可用 |
| TC-UI-014 | ChatInput 发送 Enter | P0 | UI | ✅ | 有会话 | 1. 输入 2. Enter | 文本 | 消息发出；输入框清空 |
| TC-UI-015 | ChatInput 空消息禁用 | P2 | UI | ✅ | — | 1. 空内容点发送 | — | 按钮 disabled 或无请求 |
| TC-UI-016 | TypingIndicator 流式态 | P2 | UI | ✅ | 等待回复 | 1. 发送后观察 | — | 指示器出现 |
| TC-UI-017 | StepProgress 8 阶段渲染 | P0 | UI | ✅ | 进入规划 | 1. 查看 progress | — | 需求/目的地/交通/食宿/活动/行程/确认/完成 |
| TC-UI-018 | StepProgress active 高亮 | P1 | UI | ✅ | 各阶段 | 1. 逐步推进 | 主路径 | 当前步 active；已完成 done |
| TC-UI-020 | ItineraryCard 行程卡片 | P0 | UI | ✅ | build 完成 | 1. 查看右侧/内嵌卡片 | — | 逐日+预算可见 |
| TC-UI-022 | ApprovalBanner 横幅文案 | P0 | UI | ✅ | approval 步 | 1. 查看底部 | — | 「请确认或提出修改」 |
| TC-UI-023 | ApprovalBanner 确认按钮 | P0 | UI | ✅ | Banner 可见 | 1. 点击确认 | — | 进入完成步 |
| TC-UI-024 | ApprovalBanner 修改按钮 | P0 | UI | ✅ | Banner 可见 | 1. 点击修改 | — | 触发修订 |
| TC-UI-025 | Toast 成功/错误提示 | P1 | UI | ✅ | 触发 API 错 | 1. 观察 Toast | — | 非阻塞提示 |
| TC-UI-026 | 401 Toast + 重登 | P0 | UI | ✅ | Token 失效 | 1. 任意 API 401 | — | Toast；AuthOverlay |
| TC-UI-027 | SettingsPage 入口 | P2 | UI | ✅ | 已登录 | 1. 打开设置 | — | SettingsPage 渲染 |
| TC-UI-029 | AppShell 响应式布局 | P1 | UI | ✅ | 桌面/移动 | 1. 调整宽度 | — | Sidebar/drawer 切换 |
| TC-UI-033 | 主路径 e2e UI 冒烟 | P0 | 回归 | ✅ | 全栈启动 | 1. main-path.spec | smoke 数据 | 关键步骤通过 |

### TC-UI-017 扩展说明（StepProgress 8 步）

与 `frontend/src/components/chat/StepProgress.tsx` 及 `backend/app/graph/steps.py` 对齐：

| order | id | label |
|-------|-----|-------|
| 1 | collect_requirements | 需求 |
| 2 | plan_destination | 目的地 |
| 3 | plan_transport | 交通 |
| 4 | plan_stay_and_food | 食宿 |
| 5 | plan_activities | 活动 |
| 6 | build_itinerary | 行程 |
| 7 | approval_node | 确认 |
| 8 | final_response | 完成 |

---

## 自动化映射

| 测试文件 | 覆盖用例 |
|----------|----------|
| `e2e/auth.spec.ts` | TC-UI-001~004 |
| `e2e/main-path.spec.ts` | TC-UI-006, 014, 033 |
| `e2e/revision-path.spec.ts` | TC-UI-022~024（⏳） |
| `e2e/exception-path.spec.ts` | TC-UI-031（部分） |

## 冒烟缺口（v2.0 待补）

- WebSocket 前端接入（若仅 SSE 则 TC-CHAT WS 系为后端单测）
- ApprovalBanner / ItineraryCard 专用 e2e 断言
- MobileSessionDrawer 窄屏自动化

## 流程关联

- FLOW-01~05：TC-UI-006, 017, 020~024, 033
