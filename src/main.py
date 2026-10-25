from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.routes import router as api_router

app = FastAPI(title="Events Aggregator API", description="Сервис-агрегатор для Events API")

# Обработчик ошибок валидации Pydantic: возвращаем 400 вместо 422
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors()},
    )

# Подключаем роутер с префиксом /api
app.include_router(api_router, prefix="/api")

@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}