"""Training pipeline entry point.

Run from the backend directory:

    python training/train.py

Steps (documented in README):
  1. Load + clean + engineer the dataset
  2. Split into train (70%) / validation (15%) / test (15%)
  3. Fit the preprocessing pipeline on the training split only
  4. Train the DNN (with EarlyStopping / ReduceLROnPlateau / ModelCheckpoint)
  5. Train baseline models (Linear Regression, Random Forest, Gradient Boosting)
  6. Evaluate all models on the held-out test split
  7. Save model, preprocessor, metrics, feature config and metadata
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

# Make `app` importable regardless of the working directory.
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from app.config import settings  # noqa: E402
from app.ml.preprocessor import RevenuePreprocessor  # noqa: E402
from training.evaluate import (  # noqa: E402
    permutation_importance,
    regression_metrics,
    save_history_json,
    save_plots,
)
from training.feature_engineering import load_and_engineer  # noqa: E402
from training.model import train_dnn  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("train")

SEED = 42


def _load_dataset() -> pd.DataFrame:
    processed_path = Path(settings.PROCESSED_DATA_PATH)
    if processed_path.exists():
        logger.info("Loading existing processed dataset: %s", processed_path)
        return pd.read_csv(processed_path)

    logger.info("Processed dataset not found; building from raw CSVs.")
    df = load_and_engineer(
        movies_path=settings.RAW_MOVIES_PATH,
        credits_path=settings.RAW_CREDITS_PATH,
        output_path=settings.PROCESSED_DATA_PATH,
    )
    return df


def _raw_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Convert the processed CSV frame into the raw row frame used by the pipeline."""
    raw = df.copy()
    raw["genres"] = raw["genres"].apply(_load_json_list)
    raw["lead_actors"] = raw["cast_names"].apply(_load_json_list)
    raw["release_date"] = pd.to_datetime(raw["release_date"], errors="coerce")
    return raw


def _load_json_list(value) -> list[str]:
    if isinstance(value, list):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (TypeError, json.JSONDecodeError):
        return []


def _split(raw: pd.DataFrame, test_frac: float, seed: int):
    """Stratified-by-quartile split to keep revenue ranges balanced."""
    rng = np.random.default_rng(seed)
    raw = raw.copy()
    revenue = raw["revenue"].astype(float)
    q = pd.qcut(revenue, q=4, labels=[0, 1, 2, 3], duplicates="drop")
    train_idx, val_idx, test_idx = [], [], []
    for group in q.cat.categories:
        group_idx = raw.index[q == group].to_numpy()
        rng.shuffle(group_idx)
        n_test = int(round(len(group_idx) * test_frac))
        n_val = int(round(len(group_idx) * test_frac))
        test_idx.extend(group_idx[:n_test])
        val_idx.extend(group_idx[n_test : n_test + n_val])
        train_idx.extend(group_idx[n_test + n_val :])
    rng.shuffle(train_idx)
    return raw.loc[train_idx], raw.loc[val_idx], raw.loc[test_idx]


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the box-office revenue DNN.")
    parser.add_argument("--epochs", type=int, default=settings.EPOCHS)
    parser.add_argument("--batch-size", type=int, default=settings.BATCH_SIZE)
    parser.add_argument("--learning-rate", type=float, default=settings.LEARNING_RATE)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--no-plots", action="store_true", help="Skip generating evaluation plots.")
    args = parser.parse_args()

    # 1. Dataset ------------------------------------------------------------
    df = _load_dataset()
    raw = _raw_frame(df)
    logger.info("Dataset rows: %d", len(raw))
    if len(raw) < 200:
        logger.error("Dataset too small to train (needs >= 200 rows). Got %d.", len(raw))
        sys.exit(1)

    # 2. Split --------------------------------------------------------------
    train_raw, val_raw, test_raw = _split(raw, settings.TEST_SPLIT, args.seed)
    logger.info("Split -> train=%d validation=%d test=%d", len(train_raw), len(val_raw), len(test_raw))

    y_train = np.log1p(train_raw["revenue"].astype(float).to_numpy())
    y_val = np.log1p(val_raw["revenue"].astype(float).to_numpy())
    y_test = np.log1p(test_raw["revenue"].astype(float).to_numpy())

    # 3. Preprocessing fitted on TRAINING ONLY ------------------------------
    preprocessor = RevenuePreprocessor.fit(train_raw)
    x_train = preprocessor.predict_features(train_raw)
    x_val = preprocessor.predict_features(val_raw)
    x_test = preprocessor.predict_features(test_raw)
    logger.info("Feature count: %d (numeric=%d, genre flags=%d)",
                len(preprocessor.feature_columns), len(preprocessor.numeric_columns), len(preprocessor.genre_columns))

    # 4. Train DNN -----------------------------------------------------------
    logger.info("Training DNN (epochs=%d, batch_size=%d, lr=%s)...",
                args.epochs, args.batch_size, args.learning_rate)
    model_path = str(Path(settings.MODEL_PATH))
    model, history = train_dnn(
        x_train, y_train, x_val, y_val,
        input_dim=x_train.shape[1],
        learning_rate=args.learning_rate,
        epochs=args.epochs,
        batch_size=args.batch_size,
        seed=args.seed,
        model_path=model_path,
        verbose=1,
    )

    # 5. Baselines ------------------------------------------------------------
    logger.info("Training baseline models...")
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import LinearRegression

    baselines = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=250, max_depth=18, n_jobs=-1, random_state=args.seed),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.06, random_state=args.seed),
    }
    try:
        from xgboost import XGBRegressor

        baselines["XGBoost"] = XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.06, random_state=args.seed, verbosity=0)
        logger.info("XGBoost available.")
    except ImportError:
        logger.info("XGBoost not installed; skipping.")

    baseline_predictions: dict[str, np.ndarray] = {}
    for name, estimator in baselines.items():
        estimator.fit(x_train, y_train)
        baseline_predictions[name] = estimator.predict(x_test)

    # 6. Evaluate --------------------------------------------------------------
    dnn_pred = model.predict(x_test, verbose=0).ravel()
    dnn_metrics = regression_metrics(y_test, dnn_pred)
    logger.info("DNN test metrics: %s", dnn_metrics)

    comparison = [{"model": "Deep Neural Network", **dnn_metrics}]
    for name, preds in baseline_predictions.items():
        m = regression_metrics(y_test, preds)
        comparison.append({"model": name, **m})
        logger.info("%s test metrics: %s", name, m)

    feature_names = preprocessor.feature_columns
    importance = permutation_importance(model, x_test, y_test, feature_names, n_repeats=5, seed=args.seed)

    # 7. Persist test metrics into the preprocessor (used for ranges/confidence)
    preprocessor.rmse_log = dnn_metrics["rmse_log"]
    preprocessor.mae_log = dnn_metrics["mae_log"]
    preprocessor.r2 = dnn_metrics["r2_log"]

    # 8. Save artifacts ----------------------------------------------------------
    import joblib

    Path(settings.PREPROCESSOR_PATH).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, settings.PREPROCESSOR_PATH)
    logger.info("Saved preprocessor -> %s", settings.PREPROCESSOR_PATH)

    # Re-save best model (ModelCheckpoint already wrote it; ensure it exists).
    if not Path(model_path).exists():
        model.save(model_path)
    logger.info("Saved model -> %s", model_path)

    Path(settings.EVALUATION_DIR).mkdir(parents=True, exist_ok=True)
    save_history_json(history, Path(settings.TRAINING_HISTORY_PATH))
    if not args.no_plots:
        save_plots(y_test, dnn_pred, history.history, comparison, Path(settings.EVALUATION_DIR))

    # feature_config.json
    feature_config = {
        "description": "Features available to the DNN. All are knowable before/around release.",
        "target": "revenue",
        "target_transformation": "log1p",
        "target_inverse": "expm1",
        "numeric_features": preprocessor.numeric_columns,
        "genre_features": preprocessor.genre_columns,
        "feature_columns": preprocessor.feature_columns,
        "engineered_features": [
            {
                "name": "budget_log",
                "description": "log1p(production budget USD)",
            },
            {"name": "budget_per_runtime", "description": "budget / runtime (spend intensity)"},
            {"name": "runtime", "description": "runtime in minutes"},
            {"name": "popularity", "description": "TMDB popularity score"},
            {"name": "vote_average", "description": "expected IMDb/TMDB rating 0-10"},
            {"name": "vote_count_log", "description": "log1p(expected vote count)"},
            {"name": "release_year", "description": "release year"},
            {"name": "release_month", "description": "release month 1-12"},
            {"name": "release_quarter", "description": "release quarter 1-4"},
            {"name": "release_weekday", "description": "release day of week 0-6"},
            {"name": "genre_count", "description": "number of genres"},
            {"name": "cast_size", "description": "number of lead actors"},
            {"name": "cast_star_power", "description": "max appearance frequency of lead actors in training set"},
            {"name": "director_frequency", "description": "how many movies the director has in the training set"},
            {"name": "company_frequency", "description": "how many movies the production company has in the training set"},
            {"name": "language_is_en", "description": "1 if original language is English"},
        ],
        "classification_thresholds": settings.PERFORMANCE_THRESHOLDS,
        "notes": [
            "Frequency features are identity counts (not revenue-derived), so they do not leak the target.",
            "Unknown directors/companies/actors map to frequency 0 at prediction time.",
        ],
    }
    Path(settings.FEATURE_CONFIG_PATH).write_text(json.dumps(feature_config, indent=2), encoding="utf-8")

    # metrics.json
    metrics = {
        "dataset": {
            "name": "TMDB 5000 Movie Dataset",
            "rows_used": int(len(raw)),
            "train": int(len(train_raw)),
            "validation": int(len(val_raw)),
            "test": int(len(test_raw)),
            "features": len(preprocessor.feature_columns),
            "target": "revenue (USD), trained on log1p(revenue)",
            "split": "70 / 15 / 15 (stratified by revenue quartile)",
        },
        "dnn": dnn_metrics,
        "baselines": {c["model"]: c for c in comparison if c["model"] != "Deep Neural Network"},
        "comparison": comparison,
        "feature_importance": importance,
        "architecture": {
            "layers": [
                "Input",
                "Dense(256, relu) + BatchNorm + Dropout(0.30)",
                "Dense(128, relu) + BatchNorm + Dropout(0.25)",
                "Dense(64, relu) + Dropout(0.20)",
                "Dense(32, relu)",
                "Dense(1, linear)",
            ],
            "optimizer": "Adam (lr 1e-3, ReduceLROnPlateau on plateau)",
            "loss": "Huber (delta=1.0)",
            "metric": "MAE",
        },
    }
    Path(settings.METRICS_PATH).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    logger.info("Saved metrics -> %s", settings.METRICS_PATH)

    # model_metadata.json
    import tensorflow as tf
    import platform

    metadata = {
        "model_version": settings.MODEL_VERSION,
        "model_name": "revenue_dnn",
        "model_type": "Deep Neural Network (Multi-Layer Perceptron)",
        "training_date": pd.Timestamp.now().isoformat(),
        "dataset_size": int(len(raw)),
        "feature_count": len(preprocessor.feature_columns),
        "tensorflow_version": tf.__version__,
        "keras_version": tf.keras.__version__ if hasattr(tf.keras, "__version__") else "bundled",
        "python_version": platform.python_version(),
        "framework": "TensorFlow / Keras",
        "metrics": dnn_metrics,
        "training_hyperparameters": {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "seed": args.seed,
            "early_stopping_patience": 25,
            "reduce_lr_patience": 8,
        },
    }
    Path(settings.METADATA_PATH).write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    logger.info("=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("DNN test: MAE=$%.2f  RMSE=$%.2f  R²(log)=%.4f", 
                dnn_metrics["mae_revenue"], dnn_metrics["rmse_revenue"], dnn_metrics["r2_log"])
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
