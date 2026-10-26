import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.routes import router as api_router
from src.clients.provider import EventsProviderClient
from src.db.session import async_session_maker
from src.exceptions import (
    EventNotFound,
    EventNotPublished,
    ProviderAPIError,
    RegistrationDeadlinePassed,
    SeatNotAvailable,
    TicketNotFound,
)
from src.services.sync import SyncService

logger = logging.getLogger(__name__)

async def periodic_sync():
    """Фоновая задача: синхронизация раз в 24 часа"""
    while True:
        try:
            logger.info("Starting periodic sync...")
            async with async_session_maker() as session:
                client = EventsProviderClient()
                try:
                    service = SyncService(session, client)
                    await service.sync_events()
                finally:
                    await client.close()
            logger.info("Periodic sync finished.")
        except Exception as e:
            logger.error(f"Error in periodic sync: {e}")
        
        # Ждем 24 часа (86400 секунд)
        await asyncio.sleep(86400)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запускаем фоновую задачу при старте приложения
    task = asyncio.create_task(periodic_sync())
    yield
    # Отменяем задачу при остановке
    task.cancel()

app = FastAPI(
    title="Events Aggregator API", 
    description="Сервис-агрегатор для Events API",
    lifespan=lifespan
)

# --- Обработчики ошибок ---

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.errors()})

@app.exception_handler(EventNotFound)
async def event_not_found_handler(request: Request, exc: EventNotFound):
    return JSONResponse(status_code=404, content={"detail": "Event not found"})

@app.exception_handler(TicketNotFound)
async def ticket_not_found_handler(request: Request, exc: TicketNotFound):
    return JSONResponse(status_code=404, content={"detail": "Ticket not found"})

@app.exception_handler(EventNotPublished)
async def event_not_published_handler(request: Request, exc: EventNotPublished):
    return JSONResponse(status_code=400, content={"detail": "Event is not published"})

@app.exception_handler(RegistrationDeadlinePassed)
async def deadline_passed_handler(request: Request, exc: RegistrationDeadlinePassed):
    return JSONResponse(status_code=400, content={"detail": "Registration deadline passed"})

@app.exception_handler(SeatNotAvailable)
async def seat_not_available_handler(request: Request, exc: SeatNotAvailable):
    return JSONResponse(status_code=400, content={"detail": "Seat is already taken or does not exist"})

@app.exception_handler(ProviderAPIError)
async def provider_error_handler(request: Request, exc: ProviderAPIError):
    return JSONResponse(status_code=400, content={"detail": f"Provider API error: {str(exc)}"})

# --- Роутеры ---

app.include_router(api_router, prefix="/api")

@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}