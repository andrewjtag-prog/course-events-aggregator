#!/bin/bash
set -e

echo "Waiting for postgres..."
sleep 5

export UV_CACHE_DIR=/tmp/.uv-cache

echo "Running migrations..."
# Пытаемся применить миграции до 5 раз, если база еще не готова
for i in {1..5}; do
    if uv run --no-sync alembic upgrade head; then
        echo "Migrations applied successfully!"
        break
    else
        echo "Migration failed, retrying in 5 seconds..."
        sleep 5
    fi
done

echo "Starting server..."
exec uv run --no-sync uvicorn src.main:app --host 0.0.0.0 --port 8000