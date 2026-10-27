from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.migrate import run_migrations
from app.api.auth import router as auth_router
from app.api.strategies import router as strategies_router
from app.api.instruments import router as instruments_router
from app.api.trades import router as trades_router
from app.api.attachments import router as attachments_router # <-- Import

@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield

app = FastAPI(title="Reaper's Journal API", lifespan=lifespan)

# Register routers
app.include_router(auth_router, prefix="/api")
app.include_router(strategies_router, prefix="/api")
app.include_router(instruments_router, prefix="/api")
app.include_router(trades_router, prefix="/api")
app.include_router(attachments_router, prefix="/api") # <-- Register

@app.get("/health")
def health_check():
    return {"status": "ok", "tz": settings.tz}
