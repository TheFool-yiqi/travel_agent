# API 参考

> 详细架构见 [architecture.md](architecture.md)。本页记录当前已挂载路由；未挂载的模块文件不作为可用 API。

## REST API (`/api/v1`)

| 模块 | 路由前缀 | 文件 |
|------|----------|------|
| 健康检查 | `/health`, `/api/health` | `main.py` |
| 注册 / 登录 / 当前用户 | `/users` | `api/v1/users.py` |
| 会话 | `/sessions` | `api/v1/sessions.py` |
| 会话兼容别名 | `/conversations` | `api/v1/sessions.py` |
| 对话流与历史 | `/chat` | `api/v1/chat.py` |
| 行程 | `/itineraries` | `api/v1/itineraries.py` |

当前 `auth.py`、`messages.py`、`approvals.py`、`documents.py` 文件尚未挂载到 `api_v1_router`，实现这些模块前需先确认 API 契约。

## WebSocket

| 端点 | 文件 | 说明 |
|------|------|------|
| `/api/v1/chat/ws/{conversation_id}` | `ws/chat_stream.py` | 与 SSE 同源的流式事件 |

## WS 事件类型

见 [architecture.md#52-websocket-流式规划](architecture.md)。

## 订单（MVP）

当前无独立 `orders` 表。用户确认行程后：

1. `final_response` 节点生成 `order_id`，SSE 推送 `type: order` 事件；
2. `chat_stream` 调用 `approve_itinerary_with_order`，将**最新** `itineraries` 记录标记为 `approved`；
3. 订单 payload 写入 `travel_sessions.extra_info.order`（含 `order_id`、`itinerary_id`），并同步更新 `extra_info.itinerary.status`。

若会话尚无 itinerary，`approve_itinerary_with_order` 安全返回 `None`，不会导致流式整轮失败。
