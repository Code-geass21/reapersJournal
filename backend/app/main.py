from fastapi import FastAPI
from app.config import settings

app = FastAPI(title="Reaper's Journal API")

@app.get("/health")
def health_check():
    return {"status": "ok", "tz": settings.tz}
