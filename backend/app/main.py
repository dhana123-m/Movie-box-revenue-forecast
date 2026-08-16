"""FastAPI application entry point.

Run from the backend directory:

    uvicorn app.main:app --reload

Or run the included scripts (run_backend.bat).
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup: create tables, load the model once, seed the database once."""
    Base.metadata.create_all(bind=engine)

    model_service = get_model_service()
    try:
        model_service.load()
    except Exception:
        # The health endpoint reports model_ready=false; prediction endpoints
        # return a clean MODEL_UNAVAILABLE error until artifacts exist.
        pass

    db = SessionLocal()
    try:
        seed_database(db)
    except Exception:
        pass
    finally:
        db.close()

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


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health",
    }
