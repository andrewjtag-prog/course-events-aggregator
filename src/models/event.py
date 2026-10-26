import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.place import Place


class EventStatus(str, enum.Enum):
    NEW = "new"
    PUBLISHED = "published"
    FINISHED = "finished"
    REGISTRATION_CLOSED = "registration_closed"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    place_id: Mapped[str] = mapped_column(ForeignKey("places.id"))
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registration_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[EventStatus] = mapped_column(String) #изминения типа колонки status: Mapped[EventStatus] = mapped_column(String)
    number_of_visitors: Mapped[int] = mapped_column(Integer, default=0)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    place: Mapped[Place] = relationship(lazy="joined") # Загружаем площадку сразу