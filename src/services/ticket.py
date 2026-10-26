from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.provider import EventsProviderClient
from src.models.event import EventStatus
from src.repositories.event import EventRepository
from src.repositories.ticket import TicketRepository
from src.schemas.ticket import TicketCreateSchema

_seats_cache = {}

class TicketService:
    def __init__(self, session: AsyncSession, client: EventsProviderClient):
        self.session = session
        self.client = client
        self.event_repo = EventRepository(session)
        self.ticket_repo = TicketRepository(session)

    async def get_available_seats(self, event_id: str) -> list[str]:
        """Получает свободные места (с кэшированием на 30 сек)"""
        now = datetime.now(timezone.utc).timestamp()
        
        if event_id in _seats_cache:
            cached_time, cached_seats = _seats_cache[event_id]
            if now - cached_time < 30:
                return cached_seats
        
        event = await self.event_repo.get_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        if event.status != EventStatus.PUBLISHED.value:
            raise HTTPException(status_code=400, detail="Event is not published")

        try:
            seats = await self.client.get_available_seats(event_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Provider API error: {str(e)}")
        
        _seats_cache[event_id] = (now, seats)
        return seats

    async def register_ticket(self, data: TicketCreateSchema) -> str:
        """Регистрирует билет с валидацией"""
        event = await self.event_repo.get_by_id(data.event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        if event.status != EventStatus.PUBLISHED.value:
            raise HTTPException(status_code=400, detail="Event is not published")
        
        now = datetime.now(timezone.utc)
        deadline = event.registration_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
            
        if now > deadline:
            raise HTTPException(status_code=400, detail="Registration deadline passed")

        available_seats = await self.get_available_seats(data.event_id)
        if data.seat not in available_seats:
            raise HTTPException(status_code=400, detail="Seat is already taken or does not exist")

        provider_data = {
            "first_name": data.first_name,
            "last_name": data.last_name,
            "seat": data.seat,
            "email": data.email
        }
        try:
            ticket_id = await self.client.register_ticket(data.event_id, provider_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Provider API error during registration: {str(e)}")

        await self.ticket_repo.create(
            ticket_id=ticket_id,
            event_id=data.event_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            seat=data.seat
        )
        await self.session.commit()
        
        _seats_cache.pop(data.event_id, None)
        
        return ticket_id

    async def cancel_ticket(self, ticket_id: str) -> bool:
        """Отменяет регистрацию"""
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        try:
            success = await self.client.cancel_ticket(ticket.event_id, ticket_id)
        except Exception:
            success = False
        
        await self.session.delete(ticket)
        await self.session.commit()
        
        _seats_cache.pop(ticket.event_id, None)
            
        return success