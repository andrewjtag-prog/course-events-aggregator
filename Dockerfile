FROM python:3.11-slim

WORKDIR /app

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Копируем файлы конфигурации
COPY pyproject.toml uv.lock ./

# Копируем остальной код
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini .
COPY run.sh .

# Делаем скрипт исполняемым
RUN chmod +x run.sh

# Устанавливаем зависимости (без dev-пакетов)
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["./run.sh"]