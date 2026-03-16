#!/bin/bash
# ============================================================
# Convenience script for local development
# Usage:
#   ./run-local.sh up      — start Kestra + PostgreSQL
#   ./run-local.sh down    — stop all containers
#   ./run-local.sh logs    — tail Kestra logs
#   ./run-local.sh status  — show running containers
# ============================================================

set -e

COMPOSE_FILE="docker/docker-compose.yml"
ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: .env file not found."
  echo "Run: cp .env.example .env and fill in your values."
  exit 1
fi

case "$1" in
  up)
    echo "Starting CityBikes local stack..."
    docker compose --env-file $ENV_FILE -f $COMPOSE_FILE up -d
    echo ""
    echo "Kestra UI: http://localhost:8080"
    echo "Logs: ./run-local.sh logs"
    ;;
  down)
    echo "Stopping CityBikes local stack..."
    docker compose --env-file $ENV_FILE -f $COMPOSE_FILE down
    ;;
  logs)
    docker compose --env-file $ENV_FILE -f $COMPOSE_FILE logs -f kestra
    ;;
  status)
    docker compose --env-file $ENV_FILE -f $COMPOSE_FILE ps
    ;;
  restart)
    echo "Restarting Kestra..."
    docker compose --env-file $ENV_FILE -f $COMPOSE_FILE restart kestra
    ;;
  *)
    echo "Usage: ./run-local.sh [up|down|logs|status|restart]"
    exit 1
    ;;
esac
