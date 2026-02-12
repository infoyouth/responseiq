# Dockerfile for ResponseIQ
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies
# git: required for GitClient (PR creation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*


# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project definition first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-install-project

# Copy the rest of the application
COPY . /app

# Install the project itself
RUN uv sync --frozen

# CMD to run the app
CMD ["uv", "run", "uvicorn", "responseiq.app:app", "--host", "0.0.0.0", "--port", "8000"]
