#!/bin/bash
set -e

echo "Waiting for postgres..."
sleep 3

echo "Running migrations..."
uv run alembic upgrade head

echo "Starting server..."
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000