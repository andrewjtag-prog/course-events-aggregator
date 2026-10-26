from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

# Импортируем модели, чтобы Alembic их видел
import src.models.event  
import src.models.place  
import src.models.ticket  
import src.models.sync_metadata  