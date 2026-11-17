# Dockerfile for ResponseIQ
FROM python:3.15-slim AS builder
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Native dependencies may need to compile when Python 3.15 wheels are not yet
# available. Serialize builds to avoid concurrent Rust toolchain bootstraps.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project definition first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies. Some packages may need source builds when no wheel is
# available for the selected Python version.
RUN UV_CONCURRENT_BUILDS=1 uv sync --frozen --no-install-project

# Copy the rest of the application
COPY . /app

# Install the project itself
RUN UV_CONCURRENT_BUILDS=1 uv sync --frozen

FROM python:3.15-slim
WORKDIR /app

# git: required for GitClient (PR creation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY --from=builder /app /app

# CMD to run the app
CMD ["uv", "run", "--no-sync", "uvicorn", "responseiq.app:app", "--host", "0.0.0.0", "--port", "8000"]
