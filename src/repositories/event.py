from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, select
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

    async def get_paginated_events(
        self, 
        date_from: Optional[datetime] = None, 
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[Event], int]:
        """Получает список событий с фильтрацией и пагинацией"""
        query = select(Event)
        
        if date_from:
            query = query.where(Event.event_time >= date_from)

        # Считаем общее количество
        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await self.session.execute(count_query)).scalar()

        # Пагинация
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Event.event_time)
        
        result = await self.session.execute(query)
        events = result.scalars().all()

        return list(events), total_count


class PlaceRepository(BaseRepository[Place]):
    def __init__(self, session: AsyncSession):
        super().__init__(Place, session)