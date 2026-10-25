#!/bin/bash
set -e

echo "Waiting for postgres..."
sleep 5

export UV_CACHE_DIR=/tmp/.uv-cache

echo "Running migrations..."
uv run --no-sync alembic upgrade head

echo "Starting server..."
exec uv run --no-sync uvicorn src.main:app --host 0.0.0.0 --port 8000