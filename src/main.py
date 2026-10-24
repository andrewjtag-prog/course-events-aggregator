from fastapi import FastAPI

from src.api.routes import router as api_router

app = FastAPI(title="Events Aggregator API", description="Сервис-агрегатор для Events API")

# Подключаем роутер с префиксом /api
app.include_router(api_router, prefix="/api")

@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}