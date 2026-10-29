from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
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
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Запускает синхронизацию вручную.
    Использует инкрементальную синхронизацию (берет last_changed_at из БД).
    """
    async def run_sync():
        client = request.app.state.client
        service = SyncService(db, client)
        # changed_at=None — сервис сам возьмет last_changed_at из SyncMetadata
        await service.sync_events(changed_at=None)

    background_tasks.add_task(run_sync)
    return {"status": "ok", "message": "Sync started in background"}


# --- Эндпоинты для Событий ---

@router.get("/events", response_model=PaginatedEventsSchema, tags=["Events"])
async def get_events(
    request: Request,
    date_from: Optional[str] = Query(None, description="Фильтр по дате (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db)
):
    parsed_date = None
    if date_from:
        try:
            parsed_date = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    repo = EventRepository(db)
    events, total_count = await repo.get_paginated_events(
        date_from=parsed_date, 
        page=page, 
        page_size=page_size
    )

    # Формируем ссылки на основе реального URL запроса
    base_url = request.url.remove_query_params("page")
    
    next_page = str(base_url.include_query_params(page=page+1)) if (page - 1) * page_size + page_size < total_count else None
    prev_page = str(base_url.include_query_params(page=page-1)) if page > 1 else None

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
async def get_seats(event_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Получить свободные места (кэш 30 сек)"""
    service = TicketService(db, request.app.state.client)
    seats = await service.get_available_seats(event_id)
    return {"event_id": event_id, "available_seats": seats}


@router.post("/tickets", response_model=TicketResponseSchema, status_code=201, tags=["Tickets"])
async def create_ticket(data: TicketCreateSchema, request: Request, db: AsyncSession = Depends(get_db)):
    """Регистрация на событие"""
    service = TicketService(db, request.app.state.client)
    ticket_id = await service.register_ticket(data)
    return {"ticket_id": ticket_id}


@router.delete("/tickets/{ticket_id}", tags=["Tickets"])
async def cancel_ticket(ticket_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Отмена регистрации"""
    service = TicketService(db, request.app.state.client)
    success = await service.cancel_ticket(ticket_id)
    return {"success": success}