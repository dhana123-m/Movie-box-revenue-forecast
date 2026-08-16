"""Singleton service that loads the trained DNN + preprocessing pipeline.

The Keras model is heavy, so it is loaded exactly once at application startup
(lifespan) and reused for every prediction request.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from tensorflow import keras

from ..config import settings
from ..ml.explain import SensitivityExplainer
from ..ml.preprocessor import RevenuePreprocessor
from ..utils.errors import ModelNotAvailableError

DISCLAIMER = (
    "Predictions are estimates based on historical patterns and available input features. "
    "Actual box-office performance can vary due to audience reception, competition, "
    "distribution, marketing, reviews, and other external factors."
)


class ModelService:
    def __init__(self) -> None:
        self.model = None
        self.preprocessor: RevenuePreprocessor | None = None
        self.metadata: dict = {}
        self.metrics: dict = {}
        self.feature_config: dict = {}
        self._explainer: SensitivityExplainer | None = None

    # ------------------------------------------------------------ loading ----
    def load(self) -> None:
        errors: list[str] = []

        model_path = Path(settings.MODEL_PATH)
        if not model_path.exists():
            errors.append(f"Model file not found: {model_path.name}")
        preprocessor_path = Path(settings.PREPROCESSOR_PATH)
        if not preprocessor_path.exists():
            errors.append(f"Preprocessor not found: {preprocessor_path.name}")
        if errors:
            raise ModelNotAvailableError(
                "Model artifacts are missing. Run the training pipeline "
                "(`python training/train.py`) first. " + " ".join(errors)
            )

        try:
            self.model = keras.models.load_model(str(model_path))
        except Exception as exc:  # pragma: no cover - defensive
            raise ModelNotAvailableError(f"Failed to load Keras model: {exc}") from exc

        try:
            self.preprocessor = joblib.load(str(preprocessor_path))
        except Exception as exc:  # pragma: no cover - defensive
            raise ModelNotAvailableError(f"Failed to load preprocessor: {exc}") from exc

        self.metadata = _read_json(settings.METADATA_PATH)
        self.metrics = _read_json(settings.METRICS_PATH)
        self.feature_config = _read_json(settings.FEATURE_CONFIG_PATH)
        self._explainer = SensitivityExplainer(self.model, self.preprocessor)

    @property
    def ready(self) -> bool:
        return self.model is not None and self.preprocessor is not None

    @property
    def model_version(self) -> str:
        return str(self.metadata.get("model_version", settings.MODEL_VERSION))

    def require_ready(self) -> None:
        if not self.ready:
            raise ModelNotAvailableError("Model is not loaded. Train or place the artifacts first.")

    # ---------------------------------------------------------- prediction ----
    def predict_log(self, raw_df: pd.DataFrame) -> np.ndarray:
        self.require_ready()
        vector = self.preprocessor.predict_features(raw_df)
        return self.model.predict(vector, verbose=0).reshape(-1)

    def predict_revenue(self, raw_df: pd.DataFrame) -> list[float]:
        log_preds = self.predict_log(raw_df)
        return [self.preprocessor.inverse_log1p(v[0]) for v in log_preds]

    def explain(self, raw_row: dict):
        self.require_ready()
        return self._explainer.explain(raw_row)

    def model_info(self) -> dict:
        self.require_ready()
        info = {
            "model": "Deep Neural Network (Multi-Layer Perceptron)",
            "model_version": self.model_version,
            "framework": f"TensorFlow {keras.backend.backend()}",
            "feature_count": len(self.preprocessor.feature_columns),
            "features": self.preprocessor.feature_columns,
            "numeric_features": self.preprocessor.numeric_columns,
            "genre_features": self.preprocessor.genre_columns,
            "target": "log1p(revenue)",
            "target_inverse": "expm1(log_prediction)",
            "performance_thresholds": settings.PERFORMANCE_THRESHOLDS,
            "dataset": self.metrics.get("dataset", {}),
            "training_date": self.metadata.get("training_date"),
            "metrics": self.metrics.get("dnn", {}),
            "ready": self.ready,
            "disclaimer": DISCLAIMER,
        }
        return info


_service: ModelService | None = None


def get_model_service() -> ModelService:
    global _service
    if _service is None:
        _service = ModelService()
    return _service


def _read_json(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
