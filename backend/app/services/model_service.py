"""Singleton service that loads the trained DNN + preprocessing pipeline.

The model is loaded exactly once at application startup (lifespan) and reused
for every prediction request.

Serving runtimes, in order of preference:

1. LiteRT (``.tflite`` artifact) -- a few MB, used on serverless/container
   deploys (Vercel / Render) where the full TensorFlow wheel is too heavy.
2. Keras (``.keras`` artifact)   -- fallback when only TensorFlow is
   available, e.g. local development without ai-edge-litert installed.

Both paths expose the same ``predict(X) -> (n, 1)`` interface used by
:meth:`ModelService.predict_log` and :mod:`app.ml.explain`.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ..config import settings
from ..ml.explain import SensitivityExplainer
from ..ml.preprocessor import RevenuePreprocessor
from ..utils.errors import ModelNotAvailableError

DISCLAIMER = (
    "Predictions are estimates based on historical patterns and available input features. "
    "Actual box-office performance can vary due to audience reception, competition, "
    "distribution, marketing, reviews, and other external factors."
)


def _make_interpreter(model_path: str):
    """Return a TFLite interpreter, trying every known runtime. None if absent."""
    try:
        from ai_edge_litert.interpreter import Interpreter  # type: ignore

        return Interpreter(model_path=model_path), "LiteRT"
    except ImportError:
        pass
    try:
        from tflite_runtime.interpreter import Interpreter  # type: ignore

        return Interpreter(model_path=model_path), "tflite-runtime"
    except ImportError:
        pass
    try:
        import tensorflow as tf  # type: ignore

        return tf.lite.Interpreter(model_path=model_path), "tf.lite"
    except ImportError:
        return None, None


class TFLiteModel:
    """Minimal drop-in replacement for ``keras.Model.predict`` via LiteRT."""

    def __init__(self, model_path: str | Path, runtime: str) -> None:
        self.runtime = runtime
        self.interpreter, _ = _make_interpreter(str(model_path))
        self.interpreter.allocate_tensors()
        self._input = self.interpreter.get_input_details()[0]
        self._output = self.interpreter.get_output_details()[0]

    def predict(self, X, verbose: int = 0) -> np.ndarray:
        arr = np.asarray(X, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        n_rows, n_feats = arr.shape

        try:
            if list(self._input["shape"]) != [n_rows, n_feats]:
                self.interpreter.resize_tensor_input(self._input["index"], [n_rows, n_feats])
                self.interpreter.allocate_tensors()
            self.interpreter.set_tensor(self._input["index"], arr)
            self.interpreter.invoke()
            return self.interpreter.get_tensor(self._output["index"])
        except Exception:
            # Some converters freeze the input batch to 1; fall back to a
            # row-at-a-time loop (the MLP is tiny, so this stays fast).
            self.interpreter.resize_tensor_input(self._input["index"], [1, n_feats])
            self.interpreter.allocate_tensors()
            out = np.empty((n_rows, 1), dtype=np.float32)
            for i in range(n_rows):
                self.interpreter.set_tensor(self._input["index"], arr[i : i + 1])
                self.interpreter.invoke()
                out[i] = self.interpreter.get_tensor(self._output["index"])
            return out


class ModelService:
    def __init__(self) -> None:
        self.model = None
        self.backend: str = ""
        self.preprocessor: RevenuePreprocessor | None = None
        self.metadata: dict = {}
        self.metrics: dict = {}
        self.feature_config: dict = {}
        self._explainer: SensitivityExplainer | None = None

    # ------------------------------------------------------------ loading ----
    def load(self) -> None:
        tflite_path = Path(settings.MODEL_TFLITE_PATH)
        keras_path = Path(settings.MODEL_PATH)
        preprocessor_path = Path(settings.PREPROCESSOR_PATH)

        errors: list[str] = []
        if not tflite_path.exists() and not keras_path.exists():
            errors.append(
                f"Model files not found ({tflite_path.name} / {keras_path.name})"
            )
        if not preprocessor_path.exists():
            errors.append(f"Preprocessor not found: {preprocessor_path.name}")
        if errors:
            raise ModelNotAvailableError(
                "Model artifacts are missing. Run the training pipeline "
                "(`python training/train.py`) first. " + " ".join(errors)
            )

        if tflite_path.exists():
            try:
                interpreter, runtime = _make_interpreter(str(tflite_path))
                if interpreter is not None:
                    self.model = TFLiteModel(tflite_path, runtime or "tflite")
                    self.backend = f"TensorFlow Lite ({self.model.runtime})"
            except Exception:  # pragma: no cover - defensive
                self.model = None

        if self.model is None:
            try:
                from tensorflow import keras

                self.model = keras.models.load_model(str(keras_path))
                self.backend = f"TensorFlow {keras.backend.backend()}"
            except Exception as exc:
                raise ModelNotAvailableError(
                    f"Failed to load model (tried LiteRT .tflite and Keras .keras): {exc}"
                ) from exc

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
            "framework": self.backend,
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
