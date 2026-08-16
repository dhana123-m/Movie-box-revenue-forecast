"""SQLAlchemy model for historical movies stored for the dashboard/analytics."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from ..database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, index=True, nullable=True)

    title = Column(String(255), nullable=False)
    genres = Column(Text, nullable=True)  # JSON array of genre names
    primary_genre = Column(String(80), nullable=True)
    original_language = Column(String(8), nullable=True)
    production_company = Column(String(255), nullable=True)
    director = Column(String(255), nullable=True)

    budget = Column(Float, nullable=False)
    revenue = Column(Float, nullable=False)
    runtime = Column(Float, nullable=True)
    rating = Column(Float, nullable=True)
    vote_count = Column(Integer, nullable=True)
    popularity = Column(Float, nullable=True)
    cast_size = Column(Integer, nullable=True)

    release_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    release_year = Column(Integer, nullable=True)
    release_month = Column(Integer, nullable=True)
    release_quarter = Column(Integer, nullable=True)
    release_weekday = Column(Integer, nullable=True)

    is_demo = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    @property
    def roi(self) -> float | None:
        """Return-on-investment percentage; None when budget is missing/zero."""
        if not self.budget:
            return None
        return (self.revenue - self.budget) / self.budget * 100.0
