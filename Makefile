

.PHONY: all sync install dev-install lint format format-check test test-safety coverage-test run build deploy \
	mypy security dependency-audit package-smoke lock-check docker-build docker-up ci check help \
	sand sand-v sand-payment sand-auth sand-inventory sand-fastapi sand-flask sand-setup

.NOTPARALLEL: all ci check

export UV_FROZEN := 1


all: ci  ## Run the full CI-equivalent local gate


sync:  ## Sync environment from lockfile (Hermetic)
	uv sync --frozen

install: sync  ## Install all dependencies (frozen)


dev-install:  ## Install dev dependencies
	uv sync --group dev


run:  ## Run the API server (dev mode)
	uv run uvicorn responseiq.app:app --reload


test:  ## Run all tests
	uv run pytest -n auto --dist=loadscope


test-safety:  ## Run fast regression tests for provenance, graph, and candidate isolation
	uv run pytest \
		tests/unit/test_artifact_provenance.py \
		tests/unit/test_causal_graph.py \
		tests/unit/test_sandbox_runner.py \
		tests/unit/test_worktree_service.py \
		tests/unit/test_remediation_service.py \
		tests/unit/test_llm_service.py \
		tests/unit/test_outcome_ledger.py \
		tests/unit/test_feedback.py \
		tests/unit/test_audit_service.py \
		tests/fixtures/test_sandbox_regressions.py -q


coverage-test:  ## Run the full suite with the CI branch-coverage floor
	uv run pytest -n auto --dist=loadscope --maxfail=1 --disable-warnings --cov=src/responseiq --cov-branch --cov-fail-under=80 --cov-report=term-missing -q


lint:  ## Lint code with Ruff
	uv run ruff check src tests


format:  ## Format code with Ruff
	uv run ruff format src tests


format-check:  ## Check formatting without modifying files
	uv run ruff format --check src tests


mypy:  ## Type-check code with mypy
	uv run mypy src


security:  ## Run security checks (Bandit-equivalent via Ruff)
	uv run ruff check --select S src


dependency-audit:  ## Audit dependencies without overwriting local reports
	@set -eu; audit_dir=$$(mktemp -d); trap 'rm -rf "$$audit_dir"' EXIT; \
	uv run python scripts/pip_audit_retry.py --output "$$audit_dir/pip-audit.json" --retries 3 --delay-seconds 20


package-smoke:  ## Build a wheel in a temporary directory and smoke-test its CLI
	@set -eu; smoke_dir=$$(mktemp -d); trap 'rm -rf "$$smoke_dir"' EXIT; \
	uv build --out-dir "$$smoke_dir/dist"; \
	uv venv "$$smoke_dir/venv"; \
	wheel=$$(find "$$smoke_dir/dist" -maxdepth 1 -type f -name '*.whl' -print -quit); \
	test -n "$$wheel"; \
	uv pip install --python "$$smoke_dir/venv/bin/python" "$$wheel"; \
	"$$smoke_dir/venv/bin/responseiq" --help; \
	"$$smoke_dir/venv/bin/python" -m responseiq.cli --help


lock-check:  ## Verify the lockfile is current
	env -u UV_FROZEN uv lock --check


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


# Run the same verification gates as CI locally.
ci: sync lock-check format-check lint mypy security dependency-audit test-safety coverage-test package-smoke ## Run the full CI pipeline locally

# Guard: run local checks before push without changing source files.
check: format-check lint mypy security test-safety test  ## Run local formatting, lint, type, security, and test checks

# Self-documenting help
help:  ## Show this help message
	@echo "Available targets:"; \
	grep -E '^[a-zA-Z0-9_-]+:.*?##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
