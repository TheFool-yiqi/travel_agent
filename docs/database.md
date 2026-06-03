# 数据库设计

> 详细架构见 [architecture.md](architecture.md)。

## 技术选型

- **数据库**：PostgreSQL 16 + pgvector
- **ORM**：SQLAlchemy 2.x
- **迁移**：Alembic (`backend/alembic/`)

## 表清单

| 模型文件 | 表名 | 说明 |
|----------|------|------|
| `user.py` | `users` | 用户账号 |
| `travel_session.py` | `travel_sessions` | 规划会话 |
| `message.py` | `messages` | 聊天消息 |
| `itinerary.py` | `itineraries` | 行程方案 |
| `itinerary_item.py` | `itinerary_items` | 行程条目 |
| `approval.py` | `approvals` | 审批记录 |
| `user_preference.py` | `user_preferences` | 用户偏好 |
| `document.py` | `documents` | RAG 文档元数据 |
| `document_chunk.py` | `document_chunks` | 文档切片 |

## 初始化（完整版）

业务表与 LangGraph 表可一次初始化：

```bash
# 1. 启动 PostgreSQL
docker compose up -d postgres

# 2. 完整初始化（业务表 create_all + Checkpointer + Store + pgvector）
cd backend
uv run python scripts/init_db.py

# 生产推荐：Alembic 业务表 + 同上 LangGraph 部分
uv run python scripts/init_db.py --alembic

# 仅 LangGraph / pgvector（业务表已由 Alembic 管理时）
uv run python scripts/init_db.py --skip-business
```

| 脚本 / 命令 | 职责 |
|------|------|
| `backend/scripts/init_db.py` | 业务表 + LangGraph 表 + pgvector（完整版） |
| `backend/scripts/init_db.py --alembic` | Alembic 业务表 + LangGraph + pgvector |
| `uv run alembic upgrade head` | 仅业务表迁移 |

## Checkpoint

LangGraph checkpoint 由 `langgraph-checkpoint-postgres` 管理，存储在独立表中，不落业务 ORM 模型。

## ER 图

见 [architecture.md#8-数据架构](architecture.md)。
