from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.event import Event
from src.models.place import Place
from src.repositories.base import BaseRepository

class EventRepository(BaseRepository[Event]):
    def __init__(self, session: AsyncSession):
        super().__init__(Event, session)

    async def get_with_place(self, event_id: str) -> Optional[Event]:
        """Получает событие вместе с информацией о площадке"""
        query = select(Event).where(Event.id == event_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

class PlaceRepository(BaseRepository[Place]):
    def __init__(self, session: AsyncSession):
        super().__init__(Place, session)
        