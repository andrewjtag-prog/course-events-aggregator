from sqlalchemy.ext.asyncio import AsyncSession
from src.models.ticket import Ticket
from src.repositories.base import BaseRepository

class TicketRepository(BaseRepository[Ticket]):
    def __init__(self, session: AsyncSession):
        super().__init__(Ticket, session)