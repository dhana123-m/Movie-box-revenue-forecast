"""Training / model-metrics endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..schemas.common import ok
from ..services.training_service import TrainingService
from ..utils.errors import ModelNotAvailableError

router = APIRouter(tags=["training"])


@router.get("/api/training/metrics")
def training_metrics():
    metrics_path = Path(settings.METRICS_PATH)
    if not metrics_path.exists():
        raise ModelNotAvailableError("No training metrics found. Train the model first.")
    import json

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    history = {}
    history_path = Path(settings.TRAINING_HISTORY_PATH)
    if history_path.exists():
        history = json.loads(history_path.read_text(encoding="utf-8"))

    return ok({"metrics": metrics, "training_history": history})


@router.post("/api/retrain")
def retrain(db: Session = Depends(get_db)):
    service = TrainingService()
    return ok(service.trigger(settings.ENVIRONMENT, settings.ALLOW_RETRAIN))


@router.get("/api/training/status")
def training_status():
    service = TrainingService()
    return ok(service.status())
