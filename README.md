# responseiq

[![CI](https://github.com/infoyouth/responseiq/actions/workflows/ci.yml/badge.svg)](https://github.com/infoyouth/responseiq/actions)
[![PyPI](https://img.shields.io/pypi/v/responseiq)](https://pypi.org/project/responseiq/)
[![License](https://img.shields.io/github/license/infoyouth/responseiq)](LICENSE)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **"Don't debug. Innovative fix."**

**ResponseIQ** is not just a log parser. It is the **First Self-Healing Infrastructure Copilot**.
It automatically analyzes your crash logs, physically reads your source code to understand the context, and generates surgical remediation plans to fix production incidents in seconds.

## 🚀 Quick Start

### 1. Install
```bash
pip install responseiq
```

### 2. Scan for Issues
Run from your project root:
```bash
responseiq --target ./logs --mode scan
```
_Output: Scans logs in `./logs` and reports errors found._

### 3. Auto-Fix (The Magic)
Ask ResponseIQ to analyze the code context and suggest a fix:
```bash
responseiq --target ./logs --mode fix
```

---

## Dependency Management & Virtual Environment

This project uses [UV](https://github.com/astral-sh/uv) for ultra-fast dependency installation and reproducible builds.

### Setup
1. **Create a virtual environment (recommended):**
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. **Install UV:**
   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Sync dependencies:**
   ```sh
   uv sync
   # For development dependencies:
   uv sync --group dev
   ```

### Running the App
Use UV to run the FastAPI app with hot reload:
```sh
uv run uvicorn src.app:app --reload
```

## Docker & Docker Compose

This project uses Docker and Docker Compose for consistent local and CI/CD environments.

### Setup
1. **Build and start services:**
   ```sh
   docker-compose up --build
   ```
2. **Services:**
   - `app`: FastAPI application
   - `db`: Postgres database

### Benefits
- Same environment locally and in CI/CD
- Avoids "works on my machine" issues

### Benefits
- Ultra-fast installs
- Reproducible builds
- No pip/venv overhead

## Hot Reload with Uvicorn

Hot reload is enabled for development. Use:
```sh
make run
```
This runs Uvicorn with `--reload` for instant feedback during development.

## Pre-commit Hooks

Pre-commit hooks are configured to auto lint, format, and type-check before each commit.

### Setup
1. Install pre-commit:
   ```sh
   pip install pre-commit
   ```
2. Install hooks:
   ```sh
   pre-commit install
   ```
3. Run hooks manually (optional):
   ```sh
   pre-commit run --all-files
   ```

### Benefits
- No broken code in repo
- Consistent code style and quality

## Makefile Automation

Common development tasks are automated in the Makefile:
- `make lint` → flake8
- `make format` → black + isort
- `make test` → pytest
- `make security` → bandit

Run any task with:
```sh
make <task>
```

## Live Testing with Watchdog

Continuous test reruns are enabled with [pytest-watch](https://github.com/joeyespo/pytest-watch):

Install dev dependencies:
```sh
uv sync --group dev
```
Run live tests:
```sh
uv run ptw tests/
```

## Local Observability with OpenTelemetry

Trace performance locally before production using OpenTelemetry instrumentation:

Install OpenTelemetry:
```sh
uv sync --group dev
```
Run the app with tracing:
```sh
uv run opentelemetry-instrument uvicorn src.app:app --reload
```

## Quick start

Run the app locally (development, hot reload):

```sh
# inside a virtualenv with dependencies installed
uv run uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
```

Run the unit tests:

```sh
make test
```

Example curl requests:

```sh
# Ingest a log (server will run on :8000 from above command)
curl -sS -X POST http://localhost:8000/logs \
   -H "Content-Type: application/json" \
   -d '{"message": "critical: panic when allocating resource"}' | jq

# List all incidents
curl -sS http://localhost:8000/incidents | jq

# Filter incidents by severity
curl -sS "http://localhost:8000/incidents?severity=high" | jq
```

Notes:
- The API uses Pydantic schemas (`LogIn`, `LogOut`, `IncidentOut`) and OpenAPI is available at `http://localhost:8000/docs` or `http://localhost:8000/openapi.json`.
- For integration with Postgres (production-like), run via Docker Compose.
