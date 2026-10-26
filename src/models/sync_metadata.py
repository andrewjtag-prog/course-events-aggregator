from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import Base

class SyncMetadata(Base):
    __tablename__ = "sync_metadata"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    last_sync_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_changed_at: Mapped[str] = mapped_column(String, nullable=True)
    sync_status: Mapped[str] = mapped_column(String, default="idle")