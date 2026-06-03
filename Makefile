.PHONY: help docker-up docker-down init-db backend frontend test-backend test-frontend test-e2e test-smoke test-smoke-ui docker-prod

help:
	@echo "diao-travelagent — 本地开发"
	@echo ""
	@echo "  make docker-up      启动 PostgreSQL + Redis"
	@echo "  make docker-down    停止容器"
	@echo "  make docker-prod    生产编排 (docker-compose.prod.yml)"
	@echo "  make init-db        初始化数据库 (Alembic + LangGraph 表)"
	@echo "  make backend        启动 FastAPI (默认 port 8200，见 .env APP_PORT)"
	@echo "  make frontend       启动 Vite 前端 (port 5173)"
	@echo "  make test-backend   运行后端单元测试"
	@echo "  make test-frontend  前端 build + lint"
	@echo "  make test-e2e       Playwright 全部 e2e (自动起 dev server)"
	@echo "  make test-smoke     冒烟 — 后端 pytest (-m smoke)"
	@echo "  make test-smoke-ui  冒烟 — 后端 + Playwright (需 backend 已启动)"
	@echo ""
	@echo "首次启动: docker-up -> init-db -> backend (另开终端 frontend)"
	@echo "需配置根目录 .env (MIMO_API_KEY, JWT_SECRET_KEY, DB_*)"

docker-up:
	docker compose up -d

docker-down:
	docker compose down

init-db:
	uv run python backend/scripts/init_db.py --alembic

backend:
	uv run python backend/scripts/run_server.py

frontend:
	cd frontend && npx pnpm@9.15.0 dev

test-backend:
	uv run pytest backend/tests/ -m "not integration" -q

test-frontend:
	cd frontend && npx pnpm@9.15.0 run build && npx pnpm@9.15.0 run lint

test-e2e:
	cd frontend && npx pnpm@9.15.0 run test:e2e

test-smoke:
	uv run pytest backend/tests/ -m smoke -q

test-smoke-ui: test-smoke
	cd frontend && npx pnpm@9.15.0 exec playwright test --config ../playwright.config.ts

docker-prod:
	docker compose -f docker-compose.prod.yml up -d --build
