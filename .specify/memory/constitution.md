# Travel Agent Constitution

## Core Principles

### I. Confirm Before Assume

When requirements, architecture choices, or API contracts are ambiguous, AI agents MUST ask the user for clarification before implementing. See [AGENTS.md](../AGENTS.md) Section 2.1.

### II. Layered Architecture

Respect the backend layering boundaries: `api/ws → services → graph/agents → tools/mcp → repositories`. No layer skipping.

### III. Minimal Change

Implement only what is requested. No drive-by refactors, no unsolicited features or tests.

### IV. Security First

Never commit secrets. Use `.env.example` for documentation. Real keys stay in `.env` (gitignored).

### V. Spec-Driven Development

Use Spec Kit workflow for feature development: specify → clarify → plan → tasks → implement.

## Technology Stack

- Backend: Python 3.12+, FastAPI, LangGraph, SQLAlchemy, PostgreSQL, Redis, ChromaDB
- Frontend: Vite, React, TypeScript, Tailwind, Zustand
- AI: DashScope (Qwen), DeepSeek, MiMo via `backend/app/ai/`

## Governance

- [AGENTS.md](../AGENTS.md) governs AI agent behavior
- [docs/architecture.md](../docs/architecture.md) is the technical source of truth
- Constitution amendments require user approval

**Version**: 1.0.0 | **Ratified**: 2026-05-29 | **Last Amended**: 2026-05-29
