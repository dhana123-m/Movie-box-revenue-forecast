"""FastAPI application entry point.

Run from the backend directory:

    uvicorn app.main:app --reload

Or run the included scripts (run_backend.bat).

When ``frontend/dist`` exists (i.e. after ``npm run build``), the API also
serves the static frontend on the same port with SPA fallback, so the whole
application runs on a single origin (http://localhost:8000).
"""

import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import models  # noqa: F401  (register SQLAlchemy tables)
from .config import settings
from .database import Base, SessionLocal, engine
from .routes import (
    analytics_router,
    health_router,
    model_info_router,
    movies_router,
    predict_router,
    training_router,
)
from .services.db_service import seed_database
from .services.model_service import get_model_service
from .utils.errors import register_exception_handlers

logger = logging.getLogger(__name__)

# ---------------------------------------------------------- initialisation --
_init_lock = threading.Lock()
_initialized = False


def ensure_initialized() -> None:
    """Idempotent one-time bootstrap: tables, model, seed data.

    Runs from the ASGI lifespan on normal servers (uvicorn). Serverless
    platforms (e.g. Vercel) may not fire lifespan events, so the serverless
    entrypoint (api/index.py) calls this directly; safe to call repeatedly.
    """
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return

        Base.metadata.create_all(bind=engine)

        model_service = get_model_service()
        try:
            model_service.load()
        except Exception:
            # The health endpoint reports model_ready=false; prediction
            # endpoints return a clean MODEL_UNAVAILABLE error until the
            # artifacts exist.
            pass

        db = SessionLocal()
        try:
            seed_database(db)
        except Exception:
            pass
        finally:
            db.close()

        _initialized = True


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup: create tables, load the model once, seed the database once."""
    ensure_initialized()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered movie box-office revenue forecast using a Deep Neural Network. "
        "Predicts expected revenue and commercial performance category from movie "
        "characteristics available before or around release."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(model_info_router)
app.include_router(predict_router)
app.include_router(analytics_router)
app.include_router(training_router)
app.include_router(movies_router)


# ----------------------------------------------------------- static frontend --
def _register_static_frontend() -> bool:
    """Mount the built React app (frontend/dist) when it exists.

    Returns True when the SPA was mounted, in which case all non-API GET
    routes fall back to ``index.html`` (client-side routing).
    """
    dist = Path(settings.FRONTEND_DIST_PATH)
    if not dist.is_dir():
        return False

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def _spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise StarletteHTTPException(status_code=404, detail="Not Found")
        candidate = dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(dist / "index.html")

    return True


if _register_static_frontend():
    logger.info("Serving frontend build from %s", settings.FRONTEND_DIST_PATH)
else:
    @app.get("/")
    def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/api/health",
        }
