# ============================================================
# CityBikes DE — Ingestion Container
# ============================================================
# Multi-stage build:
#   Stage 1 (builder): installs dependencies using uv
#   Stage 2 (runtime): lean image with only what's needed
# ============================================================

# --- Stage 1: builder ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first
# Docker caches this layer — if pyproject.toml and uv.lock
# haven't changed, the expensive install step is skipped
COPY ingestion/pyproject.toml ingestion/uv.lock ./

# Install dependencies into /build/.venv
# --frozen: use exact versions from uv.lock, never update
# --no-dev: skip dev dependencies (pytest, ruff, black)
RUN uv sync --frozen --no-dev

# --- Stage 2: runtime ---
FROM python:3.12-slim AS runtime

# Never run containers as root
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy the venv from builder
COPY --from=builder /build/.venv /app/.venv

# Copy application code
COPY ingestion/src/ ./src/
COPY ingestion/config/ ./config/
COPY ingestion/main.py .

# Add venv to PATH so python and all tools resolve correctly
ENV PATH="/app/.venv/bin:$PATH"

# Switch to non-root user
USER appuser

CMD ["python", "main.py"]
