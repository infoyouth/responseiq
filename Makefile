
.PHONY: all install dev-install lint format test run build deploy mypy security docker-up ci

all: ci security

install:
	uv sync

dev-install:
	uv sync --group dev

run:
	uv run uvicorn src.app:app --reload

test:
	uv run pytest

lint:
	uv run flake8 src tests

format:
	uv run black src tests && uv run isort src tests && uv run ruff check src tests --fix

mypy:
	uv run mypy src

security:
	uv run bandit -r src

build:
	docker build -t responseiq:latest .

docker-up:
	docker compose up

deploy:
	helm upgrade --install responseiq ./helm


# run the same checks as CI locally
ci:
	uv run flake8 src tests
	uv run black --check src tests
	uv run isort --check-only src tests
	uv run mypy src
	uv run pytest --maxfail=1 --disable-warnings -q
