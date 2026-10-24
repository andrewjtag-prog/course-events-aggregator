from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.ticket import Ticket
from src.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    def __init__(self, session: AsyncSession):
        super().__init__(Ticket, session)

    async def get_by_id(self, ticket_id: str) -> Ticket | None:
        """Переопределяем метод, так как в таблице Ticket первичный ключ называется ticket_id"""
        query = select(self.model).where(self.model.ticket_id == ticket_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()