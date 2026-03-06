

.PHONY: all sync install dev-install lint format test run build deploy mypy security docker-up ci check help \
        sand sand-v sand-payment sand-auth sand-inventory sand-fastapi sand-flask sand-setup

export UV_FROZEN := 1


all: sync check build format lint test mypy security ## Install, check, and build everything


sync:  ## Sync environment from lockfile (Hermetic)
	uv sync --frozen

install: sync  ## Install all dependencies (frozen)


dev-install:  ## Install dev dependencies
	uv sync --group dev


run:  ## Run the API server (dev mode)
	uv run uvicorn responseiq.app:app --reload


test:  ## Run all tests
	uv run pytest -n auto --dist=loadscope


lint:  ## Lint code with Ruff
	uv run ruff check src tests


format:  ## Format code with Ruff
	uv run ruff format src tests


mypy:  ## Type-check code with mypy
	uv run mypy src


security:  ## Run security checks (Bandit-equivalent via Ruff)
	uv run ruff check --select S src


sand:  ## Run local sandbox end-to-end demo (never pushed to remote)
	uv run python sandbox/run_demo.py

sand-v:  ## Run sandbox demo with verbose JSON output
	uv run python sandbox/run_demo.py --verbose

sand-payment:  ## Run sandbox: INC-001 payment silent failure
	uv run python sandbox/run_demo.py --incident payment

sand-auth:  ## Run sandbox: INC-002 auth KeyError + PII scrubbing
	uv run python sandbox/run_demo.py --incident auth

sand-inventory:  ## Run sandbox: INC-003 inventory pool exhaustion
	uv run python sandbox/run_demo.py --incident inventory

sand-fastapi:  ## Run sandbox: INC-004 FastAPI template (requires setup.sh)
	uv run python sandbox/run_demo.py --incident fastapi

sand-flask:  ## Run sandbox: INC-005 Flask 3.1.2 stream_with_context (requires setup.sh)
	uv run python sandbox/run_demo.py --incident flask

sand-setup:  ## Clone real GitHub repos for sandbox incidents #4 and #5
	bash sandbox/setup.sh


build:  ## Build Python package (wheel/sdist)
	uv build


docker-build:  ## Build Docker image
	docker build -t responseiq:latest .


docker-up:  ## Start Docker Compose stack
	docker compose up


deploy:  ## Deploy with Helm
	helm upgrade --install responseiq ./helm


# run the same checks as CI locally (Immutable Gate)
ci:  ## Run CI pipeline (lock, lint, type, test)
	uv lock --check
	uv run ruff check src tests --no-fix
	uv run mypy src
	uv run pytest -n auto --dist=loadscope --maxfail=1 --disable-warnings -q

# Guard: run all local checks before push
check: format lint mypy test  ## Run all local checks (format, lint, type, test)

# Self-documenting help
help:  ## Show this help message
	@echo "Available targets:"; \
	grep -E '^[a-zA-Z0-9_-]+:.*?##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
