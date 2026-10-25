#!/bin/bash
set -e

echo "Waiting for postgres..."
sleep 3

# Указываем uv использовать временную папку для кэша
export UV_CACHE_DIR=/tmp/.uv-cache

echo "Running migrations..."
uv run alembic upgrade head

echo "Starting server..."
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000