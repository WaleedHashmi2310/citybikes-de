#!/bin/bash
# ============================================================
# CityBikes DE — Local Development Convenience Script
# ============================================================
# Usage:
#   ./run-local.sh airflow-start   — start local Airflow via Astro
#   ./run-local.sh airflow-stop    — stop local Airflow
#   ./run-local.sh airflow-logs    — tail Airflow logs
#   ./run-local.sh ingest-local    — run ingestion locally to disk
#   ./run-local.sh ingest-gcs      — run ingestion against real GCS
# ============================================================

set -e

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: .env file not found."
  echo "Run: cp .env.example .env and fill in your values."
  exit 1
fi

# Load env vars
set -a && source $ENV_FILE && set +a

case "$1" in
  airflow-start)
    echo "Starting local Airflow via Astro..."
    cd airflow && astro dev start
    ;;
  airflow-stop)
    echo "Stopping local Airflow..."
    cd airflow && astro dev stop
    ;;
  airflow-logs)
    cd airflow && astro dev logs
    ;;
  ingest-local)
    echo "Running ingestion locally (writing to /tmp/citybikes)..."
    cd ingestion
    source .venv/bin/activate
    STORAGE_BACKEND=local LOCAL_STORAGE_PATH=/tmp/citybikes python main.py
    ;;
  ingest-gcs)
    echo "Running ingestion against real GCS..."
    cd ingestion
    source .venv/bin/activate
    STORAGE_BACKEND=gcs python main.py
    ;;
  *)
    echo "Usage: ./run-local.sh [airflow-start|airflow-stop|airflow-logs|ingest-local|ingest-gcs]"
    exit 1
    ;;
esac
