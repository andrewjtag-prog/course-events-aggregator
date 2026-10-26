from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.routes import router as api_router
from src.exceptions import (
    EventNotFound,
    EventNotPublished,
    RegistrationDeadlinePassed,
    SeatNotAvailable,
    TicketNotFound,
    ProviderAPIError,
)

app = FastAPI(title="Events Aggregator API", description="Сервис-агрегатор для Events API")

# --- Обработчики ошибок ---

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors()},
    )

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