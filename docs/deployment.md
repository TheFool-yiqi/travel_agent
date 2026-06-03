# 部署指南

> 详细架构见 [architecture.md](architecture.md)。

## 本地开发

```bash
make docker-up    # PostgreSQL + Redis
make backend      # FastAPI（默认 :8200）
make frontend     # Vite :5173
```

后端端口由根目录 `.env` 的 `APP_PORT` 控制；本地默认与前端代理统一为 `8200`。生产 Docker 后端固定 `8200`，nginx 将 `/api` 反代至 backend。

## Docker 构建

| 镜像 | Dockerfile |
|------|------------|
| 后端 | `infra/docker/backend.Dockerfile` |
| 前端 | `infra/docker/frontend.Dockerfile` |
| MCP | `infra/docker/mcp.Dockerfile` |

## 生产部署

```
nginx → frontend (静态) + backend (API/WS)
              ↓
        PostgreSQL + Redis + ChromaDB
```

nginx 配置：`infra/nginx/nginx.conf`

## 环境变量

生产环境通过 `.env` 或容器编排注入，参考 `.env.example`。

关键变量：

- `APP_ENV=production`
- `DEBUG=false`
- `JWT_SECRET_KEY`（强随机值）
- 各第三方 API Key
