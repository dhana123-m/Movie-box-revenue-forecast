"""SQLAlchemy model for the (single) model-metadata record."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from ..database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ModelMetadataRecord(Base):
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(20), nullable=False, default="1.0.0")
    model_type = Column(String(120), nullable=False, default="Deep Neural Network (MLP)")
    training_date = Column(DateTime, nullable=True)
    dataset_size = Column(Integer, nullable=True)
    feature_count = Column(Integer, nullable=True)
    tensorflow_version = Column(String(30), nullable=True)
    python_version = Column(String(30), nullable=True)
    metrics_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
