"""SQLAlchemy model for stored prediction records."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=True)
    movie_title = Column(String(255), nullable=True)

    input_data = Column(Text, nullable=True)  # JSON snapshot of the request
    predicted_revenue = Column(Float, nullable=False)
    performance_category = Column(String(40), nullable=True)
    model_version = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=_utcnow, nullable=False)

    movie = relationship("Movie", backref="predictions")
