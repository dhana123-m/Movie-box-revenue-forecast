"""Prediction endpoints (single, batch-by-payload and batch-by-CSV)."""

import io

import pandas as pd
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Prediction
from ..schemas.common import ok
from ..schemas.predict import BatchPredictItem, BatchPredictResponse, PredictRequest, PredictResponse
from ..services.prediction_service import PredictionService
from ..utils.errors import InvalidInputError

router = APIRouter(tags=["predict"])


@router.post("/api/predict")
def predict(payload: PredictRequest, db: Session = Depends(get_db)):
    service = PredictionService()
    result = service.predict(payload)

    db.add(
        Prediction(
            movie_title=payload.title,
            input_data=payload.model_dump_json(),
            predicted_revenue=result.predicted_revenue,
            performance_category=result.performance_category,
            model_version=result.model_version,
        )
    )
    db.commit()
    return ok(result.model_dump())


@router.post("/api/predict/batch")
def predict_batch(payload: list[BatchPredictItem]):
    service = PredictionService()
    return ok(service.predict_batch(payload).model_dump())


@router.post("/api/predict/csv")
async def predict_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise InvalidInputError("Only CSV files are accepted.")

    raw = await file.read()
    if len(raw) > settings.MAX_UPLOAD_BYTES:
        raise InvalidInputError("File exceeds the 5 MB upload limit.")

    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:
        raise InvalidInputError(f"Could not parse the CSV file: {exc}") from exc

    service = PredictionService()
    result = service.predict_csv(df)
    return ok(
        {
            "total_rows": result.total_rows,
            "successful": result.successful,
            "failed": result.failed,
            "results": [r.model_dump() for r in result.results],
        }
    )
