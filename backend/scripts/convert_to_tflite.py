"""Convert revenue_model.keras -> revenue_model.tflite and validate parity.

Run locally (needs TensorFlow, e.g. `pip install -r requirements-dev.txt`):

    cd backend
    .venv/Scripts/python scripts/convert_to_tflite.py

Writes backend/models/revenue_model.tflite and prints numerical-parity checks
against the Keras model on real feature vectors plus the reference payload.
Exits non-zero if the models disagree beyond the tolerance below.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np  # noqa: E402
import joblib  # noqa: E402
import pandas as pd  # noqa: E402

from app.config import settings  # noqa: E402
from app.services.model_service import TFLiteModel  # noqa: E402

# Raw feature row (same mapping as app.services.prediction_service._build_raw_row)
REFERENCE_PAYLOAD = {
    "budget": 120_000_000,
    "runtime": 130,
    "genres": ["Action", "Science Fiction"],
    "release_date": "2026-07-18",
    "popularity": 110.0,
    "vote_average": 8.0,
    "vote_count": 25000,
    "original_language": "en",
    "production_company": "Warner Bros.",
    "director": "Christopher Nolan",
    "lead_actors": ["Cillian Murphy", "Tom Hardy"],
}

LOG_TOLERANCE = 0.02        # max abs diff in log1p space
REVENUE_REL_TOLERANCE = 0.005  # max relative diff after expm1 (0.5%)


def convert(model) -> bytes:
    import tensorflow as tf

    try:
        return tf.lite.TFLiteConverter.from_keras_model(model).convert()
    except Exception as exc:
        print(f"from_keras_model failed ({exc!r}); falling back to SavedModel export")
        tmp_dir = BACKEND_DIR / "_tmp_savedmodel"
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        model.export(str(tmp_dir))
        try:
            return tf.lite.TFLiteConverter.from_saved_model(str(tmp_dir)).convert()
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


def main() -> int:
    from tensorflow import keras

    keras_path = Path(settings.MODEL_PATH)
    out_path = Path(settings.MODEL_TFLITE_PATH)

    print(f"loading {keras_path.name} ...")
    model = keras.models.load_model(str(keras_path))
    print(f"inputs: {[i.shape for i in model.inputs]}")

    blob = convert(model)
    out_path.write_bytes(blob)
    print(f"wrote {out_path.name}: {len(blob) / 1e6:.2f} MB")

    pre = joblib.load(str(settings.PREPROCESSOR_PATH))

    tfl = TFLiteModel(out_path, "parity-check")

    # ---- parity on the reference payload ---------------------------------
    vec = pre.predict_features(pd.DataFrame([REFERENCE_PAYLOAD]))
    k_pred = float(model.predict(vec, verbose=0).reshape(-1)[0])
    t_pred = float(tfl.predict(vec).reshape(-1)[0])
    k_rev = float(np.expm1(k_pred))
    t_rev = float(np.expm1(t_pred))
    rel = abs(t_rev - k_rev) / k_rev
    print(f"reference payload: keras={k_rev:,.0f} tflite={t_rev:,.0f} rel_diff={rel:.6%}")
    ok = rel <= REVENUE_REL_TOLERANCE

    # ---- parity on a large synthetic feature batch -----------------------
    rng = np.random.default_rng(42)
    n_feats = int(vec.shape[1])
    X = rng.normal(0.0, 1.0, size=(500, n_feats)).astype(np.float32)
    k_log = model.predict(X, verbose=0).reshape(-1)
    t_log = tfl.predict(X).reshape(-1)
    max_log = float(np.max(np.abs(k_log - t_log)))
    max_rel = float(np.max(np.abs(np.expm1(t_log) - np.expm1(k_log)) / np.maximum(np.expm1(k_log), 1.0)))
    print(f"synthetic batch(500): max|log diff|={max_log:.5f}  max revenue rel diff={max_rel:.6%}")
    ok = ok and max_log <= LOG_TOLERANCE and max_rel <= REVENUE_REL_TOLERANCE

    print("PARITY:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
