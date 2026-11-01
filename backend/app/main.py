from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.migrate import run_migrations

# Import all routers
from app.api.auth import router as auth_router
from app.api.strategies import router as strategies_router
from app.api.instruments import router as instruments_router
from app.api.trades import router as trades_router
from app.api.attachments import router as attachments_router
from app.api.prices import router as prices_router
from app.api.dashboard import router as dashboard_router
from app.api.backup import router as backup_router
from app.api.restore import router as restore_router
from app.api.alerts import router as alerts_router # <-- NEW IMPORT

@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield

# Declare the app FIRST
app = FastAPI(title="Reaper's Journal API", lifespan=lifespan)

# Register routers AFTER the app is declared
app.include_router(auth_router, prefix="/api")
app.include_router(strategies_router, prefix="/api")
app.include_router(instruments_router, prefix="/api")
app.include_router(trades_router, prefix="/api")
app.include_router(attachments_router, prefix="/api")
app.include_router(prices_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(backup_router, prefix="/api")
app.include_router(restore_router, prefix="/api")
app.include_router(alerts_router, prefix="/api") # <-- NEW ROUTER REGISTRATION

@app.get("/health")
def health_check():
    return {"status": "ok", "tz": settings.tz}
