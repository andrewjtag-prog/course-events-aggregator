#!/bin/bash
set -e

echo "Waiting for postgres..."
sleep 5

export UV_CACHE_DIR=/tmp/.uv-cache

echo "Running migrations..."
# Пытаемся применить миграции, пока не получится (или пока не истекут 10 попыток)
for i in {1..10}; do
    if uv run --no-sync alembic upgrade head; then
        echo "Migrations applied successfully!"
        break
    else
        echo "Migration failed, retrying in 3 seconds..."
        sleep 3
    fi
done

echo "Starting server..."
exec uv run --no-sync uvicorn src.main:app --host 0.0.0.0 --port 8000