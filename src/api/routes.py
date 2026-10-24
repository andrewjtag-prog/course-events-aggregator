from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.provider import EventsProviderClient
from src.db.session import get_db
from src.models.event import Event
from src.repositories.event import EventRepository
from src.schemas.event import EventDetailSchema, PaginatedEventsSchema
from src.schemas.ticket import (
    SeatsResponseSchema,
    TicketCreateSchema,
    TicketResponseSchema,
)
from src.services.sync import SyncService
from src.services.ticket import TicketService

router = APIRouter()

# --- Эндпоинты для Синхронизации ---

@router.post("/sync/trigger", tags=["Sync"], status_code=200)
async def trigger_sync(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Запускает синхронизацию вручную.
    """
    async def run_sync():
        client = EventsProviderClient()
        service = SyncService(db, client)
        await service.sync_events(changed_at="2000-01-01")
        await client.close()

    background_tasks.add_task(run_sync)
    return {"status": "ok", "message": "Sync started in background"}


# --- Эндпоинты для Событий ---

@router.get("/events", response_model=PaginatedEventsSchema, tags=["Events"])
async def get_events(
    date_from: Optional[str] = Query(None, description="Фильтр по дате (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db)
):
    query = select(Event)
    
    if date_from:
        try:
            # Преобразуем строку в datetime и добавляем таймзону UTC
            parsed_date = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            query = query.where(Event.event_time >= parsed_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    # ... дальше идет подсчет count и пагинация ...

    # Считаем общее количество для пагинации
    count_query = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(count_query)).scalar()

    # Применяем пагинацию
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Event.event_time)
    
    result = await db.execute(query)
    events = result.scalars().all()

    # Формируем ссылки для пагинации (опционально, но по заданию нужно)
    next_page = f"http://127.0.0.1:8000/api/events?page={page+1}&page_size={page_size}" if offset + page_size < total_count else None
    prev_page = f"http://127.0.0.1:8000/api/events?page={page-1}&page_size={page_size}" if page > 1 else None

    return {
        "count": total_count,
        "next": next_page,
        "previous": prev_page,
        "results": events
    }


@router.get("/events/{event_id}", response_model=EventDetailSchema, tags=["Events"])
async def get_event_detail(event_id: str, db: AsyncSession = Depends(get_db)):
    """
    Получает детали конкретного события из локальной БД.
    """
    repo = EventRepository(db)
    event = await repo.get_with_place(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    return event

@router.get("/events/{event_id}/seats", response_model=SeatsResponseSchema, tags=["Events"])
async def get_seats(event_id: str, db: AsyncSession = Depends(get_db)):
    """Получить свободные места (кэш 30 сек)"""
    client = EventsProviderClient()
    try:
        service = TicketService(db, client)
        seats = await service.get_available_seats(event_id)
        return {"event_id": event_id, "available_seats": seats}
    finally:
        await client.close()

@router.post("/tickets", response_model=TicketResponseSchema, status_code=201, tags=["Tickets"])
async def create_ticket(data: TicketCreateSchema, db: AsyncSession = Depends(get_db)):
    """Регистрация на событие"""
    client = EventsProviderClient()
    try:
        service = TicketService(db, client)
        ticket_id = await service.register_ticket(data)
        return {"ticket_id": ticket_id}
    finally:
        await client.close()

@router.delete("/tickets/{ticket_id}", tags=["Tickets"])
async def cancel_ticket(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """Отмена регистрации"""
    client = EventsProviderClient()
    try:
        service = TicketService(db, client)
        success = await service.cancel_ticket(ticket_id)
        return {"success": success}
    finally:
        await client.close()