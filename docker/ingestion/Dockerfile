# ============================================================
# CityBikes DE — Ingestion Container
# ============================================================
# Multi-stage build:
#   Stage 1 (builder): installs dependencies
#   Stage 2 (runtime): lean image with only what's needed to run
#
# This keeps the final image small and avoids shipping build
# tools into production.
# ============================================================

# --- Stage 1: builder ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy only the requirements file first.
# Docker caches layers — if requirements.txt hasn't changed,
# this expensive pip install step is skipped on rebuild.
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir --target=/build/packages -r requirements.txt

# --- Stage 2: runtime ---
FROM python:3.12-slim AS runtime

# Never run containers as root — security best practice
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /build/packages /usr/local/lib/python3.12/site-packages/

# Copy the application source code
COPY src/ ./src/
COPY config/ ./config/
COPY main.py .

# Switch to non-root user
USER appuser

# This is the command Docker runs when the container starts.
# Cloud Run Jobs execute this and then exit.
CMD ["python", "main.py"]
