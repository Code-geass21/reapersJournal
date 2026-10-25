from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.migrate import run_migrations
from app.api.auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield

app = FastAPI(title="Reaper's Journal API", lifespan=lifespan)

# This maps the router to /api/auth
app.include_router(auth_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok", "tz": settings.tz}
