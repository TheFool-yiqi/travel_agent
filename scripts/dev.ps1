# diao-travelagent 鏈湴寮€鍙戣剼鏈?(Windows PowerShell)
# 鐢ㄦ硶: .\scripts\dev.ps1 help | docker-up | docker-down | docker-prod | init-db | backend | frontend | test-backend | test-frontend | test-e2e

param(
    [Parameter(Position = 0)]
    [ValidateSet("help", "docker-up", "docker-down", "docker-prod", "init-db", "backend", "frontend", "test-backend", "test-frontend", "test-e2e")]
    [string]$Command = "help"
)

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Show-Help {
    Write-Host "diao-travelagent - local dev"
    Write-Host ""
    Write-Host "  .\scripts\dev.ps1 docker-up      鍚姩 PostgreSQL + Redis"
    Write-Host "  .\scripts\dev.ps1 docker-down    鍋滄瀹瑰櫒"
    Write-Host "  .\scripts\dev.ps1 docker-prod    鐢熶骇缂栨帓 (docker-compose.prod.yml)"
    Write-Host "  .\scripts\dev.ps1 init-db        鍒濆鍖栨暟鎹簱 (鍚?itineraries 杩佺Щ)"
    Write-Host "  .\scripts\dev.ps1 backend        鍚姩 FastAPI (榛樿 8200)"
    Write-Host "  .\scripts\dev.ps1 frontend       鍚姩 Vite 鍓嶇"
    Write-Host "  .\scripts\dev.ps1 test-backend   鍚庣鍗曞厓娴嬭瘯"
    Write-Host "  .\scripts\dev.ps1 test-frontend  鍓嶇 build + lint"
    Write-Host "  .\scripts\dev.ps1 test-e2e       Playwright 鍐掔儫"
    Write-Host ""
    Write-Host "棣栨: docker-up -> init-db -> backend (鍙﹀紑缁堢 frontend)"
}

switch ($Command) {
    "help" { Show-Help }
    "docker-up" { docker compose up -d }
    "docker-down" { docker compose down }
    "docker-prod" { docker compose -f docker-compose.prod.yml up -d --build }
    "init-db" { uv run python backend/scripts/init_db.py --alembic }
    "backend" { uv run python backend/scripts/run_server.py }
    "frontend" { Set-Location frontend; npx pnpm@9.15.0 dev }
    "test-backend" { uv run pytest backend/tests/ -m 'not integration' -q }
    "test-frontend" {
        Set-Location frontend
        npx pnpm@9.15.0 run build
        npx pnpm@9.15.0 run lint
    }
    "test-e2e" {
        Set-Location frontend
        npx pnpm@9.15.0 run test:e2e
    }
}

