from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from src.db.session import get_db
from src.models.event import Event
from src.repositories.event import EventRepository
from src.clients.provider import EventsProviderClient
from src.services.sync import SyncService
from src.schemas.event import PaginatedEventsSchema, EventDetailSchema

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
    """
    Получает список событий из локальной БД с фильтрацией и пагинацией.
    """
    query = select(Event)
    
    # Фильтрация по дате (если передана)
    if date_from:
        query = query.where(Event.event_time >= date_from)

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