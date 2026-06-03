# P2 开发任务分解

> 阶段目标：补齐 AGENTS.md / langgraph_flow.md 中 P0/P1 未覆盖的能力（Markdown、路由、活动规划、审批修订、预算质检）。  
> 约束：保持 SSE 流式、不引入 WebSocket、不新增独立 critic 图节点。

---

## P2.1 Markdown 消息

| 项 | 说明 |
|----|------|
| 范围 | 助手消息在 `MessageBubble` 中用 `react-markdown` 渲染；用户消息保持纯文本 |
| 样式 | `index.css` 增加 `.markdown-prose` 最小排版（标题、列表、代码、链接） |
| 依赖 | `react-markdown`，可选 `remark-gfm`（表格/删除线） |
| 验收 | 行程输出中的 `**Day N**`、列表在气泡内正确显示 |

---

## P2.2 React Router

| 项 | 说明 |
|----|------|
| 范围 | `react-router-dom`：`/` → 聊天主页，`/settings` → 占位设置页 |
| 重构 | `App.tsx` 使用 `BrowserRouter`；已登录时渲染 `Routes`，未登录仍显示 `AuthOverlay` |
| 设置页 | 展示品牌名、返回首页链接、`logout()` |
| 验收 | 刷新 `/settings` 不 404（Vite SPA fallback 已有）；登录态与 P1 一致 |

---

## P2.3 plan_activities 节点

| 项 | 说明 |
|----|------|
| 范围 | 新建 `graph/nodes/plan_activities.py`，模式对齐 `plan_stay_and_food` |
| 状态 | `selected_activity_types: list[str]`（culture / nature / food_tour / shopping / family_fun） |
| 图 | `plan_stay_and_food` → `plan_activities` → `build_itinerary` |
| 同步 | `steps.py`、`rollback.py`、`step_config.py`、`step_router.py`、`chat_stream` STEP 标签、`StepProgress.tsx` |
| Prompt | `ai/prompts/plan_activities.md` |
| 验收 | 食宿完成后进入活动偏好收集，再生成行程 |

---

## P2.4 审批与修订（MVP）

| 项 | 说明 |
|----|------|
| 节点 | `approval_node`：`build_itinerary` 成功后 `approval_status=pending`，询问确认后 `END` 等待下轮用户输入 |
| 修订 | `revise_itinerary`：关键词/规则识别「修改」意图，清空 `approval_status` 并 `current_step=build_itinerary` |
| 路由 | `approval_router.py`：`route_after_itinerary` → `approval_node`；`route_after_approval` → `final_response` / `revise_itinerary` / `END` |
| 确认 | 用户输入含「确认」「同意」等 → `approved` → `final_response` |
| SSE | `approval_required` 事件；前端 `ApprovalBanner`（确认 / 请求修改按钮发送固定文案） |
| 不做 | LangGraph interrupt/checkpoint 人工挂起（对话式确认即可） |

---

## P2.5 预算质检（critic 内联）

| 项 | 说明 |
|----|------|
| 范围 | 在 `build_itinerary` 返回前比较 `budget.total` 与 `user_requirement.budget_max` |
| 输出 | 超支时写入 `report` 警告并追加到助手消息 |
| 不做 | 独立 `critic_agent` 图节点 |

---

## 验证清单（Part C）

```bash
.venv\Scripts\python.exe -m pytest backend/tests/ -q --ignore=tests/integration
cd frontend && pnpm run build
```

新增测试（轻量）：

- `test_approval_router.py` — 路由函数表驱动
- `test_plan_activities.py` — 模块导入与完成条件
- `test_build_itinerary.py` — `budget_warning` 辅助函数（如有抽取）

---

## 延后至 P3（本阶段仅记录）

| 项 | 说明 |
|----|------|
| WebSocket | 替代/补充 SSE 的 `useTravelStream` |
| 行程 API | 独立 `/itineraries` 与 DB 表持久化 |
| 生产 Docker | `infra/` 完整编排与 CI 镜像 |
| E2E | Playwright/Cypress 自动化 |
