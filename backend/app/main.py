import uuid
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.migrate import run_migrations
from app.database import SessionLocal
from app.services import log_service

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
from app.api.alerts import router as alerts_router
from app.api.settings import router as settings_router
from app.api.logs import router as logs_router
from app.api.help import router as help_router
from app.api.users import router as users_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield

app = FastAPI(title="Reaper's Journal API", lifespan=lifespan)

# --- BATCH 5: Request ID Middleware ---
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(RequestIDMiddleware)

# --- BATCH 5: Global Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catches all unhandled 500 errors and writes the traceback to app_logs."""
    request_id = getattr(request.state, "request_id", "unknown")
    error_trace = traceback.format_exc()

    # Try to grab the DB session to log the error
    db: Session = SessionLocal()
    try:
        log_service.write(
            db=db,
            action=f"Unhandled Exception: {request.method} {request.url.path}",
            level="ERROR",
            source="api",
            error_text=error_trace,
            request_id=request_id
        )
    except Exception as log_exc:
        print(f"CRITICAL: Failed to write to app_logs during exception handling: {log_exc}")
    finally:
        db.close()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error", "request_id": request_id}
    )

# Register routers
app.include_router(auth_router, prefix="/api")
app.include_router(strategies_router, prefix="/api")
app.include_router(instruments_router, prefix="/api")
app.include_router(trades_router, prefix="/api")
app.include_router(attachments_router, prefix="/api")
app.include_router(prices_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(backup_router, prefix="/api")
app.include_router(restore_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(help_router, prefix="/api")
app.include_router(users_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok", "tz": settings.tz}
