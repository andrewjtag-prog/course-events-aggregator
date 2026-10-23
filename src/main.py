from fastapi import FastAPI

app = FastAPI(title="Events Aggregator API")

@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}