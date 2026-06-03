# LangGraph 流程文档

> 详细架构见 [architecture.md](architecture.md)。

## 状态定义

- 文件：`backend/app/graph/state.py`
- Reducer：`backend/app/graph/reducers.py`

## 节点列表

| 节点 | 文件 | 说明 |
|------|------|------|
| 注入用户记忆 | `nodes/inject_memory.py` | 从长期记忆读取偏好并注入 SystemMessage；可按当前进度跳转回对应节点 |
| 收集需求 | `nodes/collect_requirements.py` | 解析用户旅行需求，追问缺失信息 |
| 目的地规划 | `nodes/plan_destination.py` | 目的地选择与景点推荐 |
| 交通规划 | `nodes/plan_transport.py` | 航班/火车等大交通 |
| 住宿餐饮 | `nodes/plan_stay_and_food.py` | 酒店与餐厅 |
| 活动规划 | `nodes/plan_activities.py` | 每日活动安排 |
| 行程整合 | `nodes/build_itinerary.py` | 合并为完整行程，含预算校验 |
| 人工审批 | `nodes/approval_node.py` | interrupt 等待用户确认 |
| 行程修订 | `nodes/revise_itinerary.py` | 根据反馈修改 |
| 最终回复 | `nodes/final_response.py` | 格式化输出 |

## 条件路由

| Router | 文件 |
|--------|------|
| 需求路由 | `routers/requirement_router.py` |
| 审批路由 | `routers/approval_router.py` |
| 错误路由 | `routers/error_router.py` |

## Checkpoint 与审批

- Checkpoint：`graph/checkpoint.py`（PostgresSaver / RedisSaver 后端选择）
- 命令：`graph/commands.py`（resume 封装）
- 事件：SSE / WS 由 `services/chat_stream.py` 统一生成 `token`, `step`, `itinerary`, `approval_required`, `done`, `error`

当前审批是对话式暂停：`approval_node` 写入 `approval_status=pending` 并结束本轮，下一轮用户确认或要求修改后由 checkpoint 恢复到 `final_response` 或 `revise_itinerary`。

## 流程图

见 [architecture.md#6-langgraph-规划流程](architecture.md)。
