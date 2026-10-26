from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

# Импортируем модели, чтобы Alembic их видел
