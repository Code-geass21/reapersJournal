from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.migrate import run_migrations

@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield

app = FastAPI(title="Reaper's Journal API", lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "ok", "tz": settings.tz}
