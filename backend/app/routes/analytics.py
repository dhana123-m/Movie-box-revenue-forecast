"""Analytics endpoints computed from the stored historical movie data."""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.common import ok
from ..services.analytics_service import AnalyticsService

router = APIRouter(tags=["analytics"])


@router.get("/api/analytics/overview")
def analytics_overview(db: Session = Depends(get_db)):
    return ok(AnalyticsService(db).overview().model_dump())


@router.get("/api/analytics/genres")
def analytics_genres(db: Session = Depends(get_db)):
    data = AnalyticsService(db).genres()
    return ok([item.model_dump() for item in data])


@router.get("/api/analytics/yearly")
def analytics_yearly(min_year: Optional[int] = None, db: Session = Depends(get_db)):
    data = AnalyticsService(db).yearly(min_year=min_year)
    return ok([item.model_dump() for item in data])


@router.get("/api/analytics/budget-vs-revenue")
def analytics_budget_vs_revenue(limit: int = 500, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 2000))
    data = AnalyticsService(db).budget_vs_revenue(limit=limit)
    return ok([item.model_dump() for item in data])


@router.get("/api/analytics/top-movies")
def analytics_top_movies(limit: int = 10, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    data = AnalyticsService(db).top_movies(limit=limit)
    return ok([item.model_dump() for item in data])


@router.get("/api/analytics/release-months")
def analytics_release_months(db: Session = Depends(get_db)):
    return ok(AnalyticsService(db).release_month_performance())


@router.get("/api/analytics/genres-by-year")
def analytics_genres_by_year(db: Session = Depends(get_db)):
    return ok(AnalyticsService(db).genre_revenue_by_year())
