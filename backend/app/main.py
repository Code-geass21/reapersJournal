from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.migrate import run_migrations
from app.api.auth import router as auth_router
from app.api.strategies import router as strategies_router  # <-- Import the new router

@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield

app = FastAPI(title="Reaper's Journal API", lifespan=lifespan)

# Register routers
app.include_router(auth_router, prefix="/api")
app.include_router(strategies_router, prefix="/api")        # <-- Register it here

@app.get("/health")
def health_check():
    return {"status": "ok", "tz": settings.tz}
