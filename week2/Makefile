.DEFAULT_GOAL := help

BACKEND_HOST ?= 127.0.0.1
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 5173

.PHONY: help install run backend frontend test test-backend test-frontend lint

help:
	@echo "Chip In development commands (run from week2/)"
	@echo "  make install        Install backend dependencies with uv"
	@echo "  make run            Start the backend with automatic reload"
	@echo "  make backend        Same as make run"
	@echo "  make frontend       Start the frontend in a separate terminal"
	@echo "  make test           Run backend and frontend tests"
	@echo "  make test-backend   Run backend tests"
	@echo "  make test-frontend  Run frontend tests"
	@echo "  make lint           Check backend Python code with Ruff"
	@echo ""
	@echo "Backend docs: http://$(BACKEND_HOST):$(BACKEND_PORT)/docs"
	@echo "Frontend:     http://localhost:$(FRONTEND_PORT)"
	@echo "Override ports: make run BACKEND_PORT=8001"
	@echo "The frontend still uses mock data. Backend data resets on restart."

install:
	cd backend && uv sync --locked

run: backend

backend:
	cd backend && uv run --locked uvicorn app.main:app --reload --host $(BACKEND_HOST) --port $(BACKEND_PORT)

frontend:
	PORT=$(FRONTEND_PORT) npm --prefix frontend run dev

test: test-backend test-frontend

test-backend:
	cd backend && uv run --locked pytest

test-frontend:
	npm --prefix frontend test

lint:
	cd backend && uv run --locked ruff check .
