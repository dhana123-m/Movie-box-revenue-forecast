"""Health endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Movie
from ..schemas.common import ok
from ..services.model_service import get_model_service

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health(db: Session = Depends(get_db)):
    model_service = get_model_service()
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    movie_count = 0
    if db_ok:
        try:
            movie_count = len(db.execute(select(Movie.id)).scalars().all())
        except Exception:
            movie_count = 0

    return ok(
        {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": "connected" if db_ok else "unavailable",
            "movies_in_database": movie_count,
            "model_ready": model_service.ready,
            "model_version": model_service.model_version if model_service.ready else None,
        }
    )
