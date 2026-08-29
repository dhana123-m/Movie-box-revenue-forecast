r"""Builds notebooks/train_model.ipynb mirroring the backend training pipeline.

Run (from repo root, with backend venv that has nbformat + tensorflow):

    & "backend\.venv\Scripts\python.exe" scripts\build_train_notebook.py

The notebook reuses the exact production code (app.ml.preprocessor, training.*)
so there is a single source of truth for the model.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import nbformat as nbf

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "notebooks" / "train_model.ipynb"

nb = nbf.v4.new_notebook()
nb.metadata["kernelspec"] = {
    "name": "python3",
    "display_name": "Python 3 (ipykernel)",
    "language": "python",
}
nb.metadata["language_info"] = {"name": "python"}

cells = []


def md(text: str, remainder: dict | None = None) -> None:
    cells.append(nbf.v4.new_markdown_cell(text))


def code(code: str, remainder: dict | None = None) -> None:
    c = nbf.v4.new_code_cell(code)
    cells.append(c)


md(
    """# 🎬 Movie Box Office Revenue Forecast — Model Training

This notebook trains the **Deep Neural Network** that powers the production API,
exactly mirroring the CLI pipeline in `backend/training/train.py`. It reuses the
same canonical modules — `app.ml.preprocessor` (feature engineering/scaling) and
`training.*` (architecture, evaluation) — so the notebook is never out of sync
with the deployed model.

**What you'll do here:**

1. Load the (already-cleaned) processed dataset — or rebuild it from the raw TMDB CSVs.
2. Split into **train / validation / test** (70 / 15 / 15, stratified by revenue quartile).
3. Fit the feature-engineering preprocessor on **train only** (avoids target leakage).
4. Train the **DNN (MLP)** with EarlyStopping / ReduceLROnPlateau / ModelCheckpoint.
5. Train 8 baseline models (linear, tree, boosting, neighbors, …) for comparison.
6. Evaluate everything on the held-out test set and save plots + JSON artifacts.

When this notebook runs, it writes the production artifacts under `backend/models/`:

| Artifact | Purpose |
|---|---|
| `revenue_model.keras` | Trained Keras DNN (serving fallback) |
| `preprocessor.pkl` | Fitted preprocessor (used at predict time) |
| `metrics.json`, `model_metadata.json`, `feature_config.json` | Model info for the API |
| `evaluation/training_history.json` + `*.png` | Training curves, plots |

> **Prerequisite:** run the cells from the **`backend`** kernel path (so
> `app` / `training` packages are importable) and use a Python 3.12 environment
> with TensorFlow installed: `pip install -r requirements-dev.txt`.
> The **processed CSV is already committed** at `backend/data/processed/tmdb_5000_processed.csv`,
> so cell 1 uses that by default and skips the slow raw rebuild."""
)


md("""## 0. Setup

Point Python at the backend folder and silence TensorFlow's chatty logs.""")
code(
    """import os
import sys
import json
from pathlib import Path

# Make `app` and `training` importable regardless of the notebook working dir.
BACKEND_DIR = Path.cwd() if (Path.cwd() / "app").exists() else Path.cwd().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import numpy as np
import pandas as pd
print("cwd:", BACKEND_DIR)"""
)

md(
    """## 1. Load the dataset

The processed CSV is committed, so we load it directly. If it's missing we rebuild
it from the raw TMDB CSVs via `training.feature_engineering.load_and_engineer`."""
)
code(
    """from app.config import settings
from training.feature_engineering import load_and_engineer

processed_path = Path(settings.PROCESSED_DATA_PATH)
if processed_path.exists():
    df = pd.read_csv(processed_path)
    print(f"Loaded processed dataset: {len(df)} rows")
else:
    print("Processed dataset not found - building from raw CSVs...")
    df = load_and_engineer(
        movies_path=settings.RAW_MOVIES_PATH,
        credits_path=settings.RAW_CREDITS_PATH,
        output_path=settings.PROCESSED_DATA_PATH,
    )

df.head()"""
)
code(
    """# Convert the processed frame into the raw row frame the pipeline expects.
def _load_json_list(value):
    if isinstance(value, list):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (TypeError, json.JSONDecodeError):
        return []

raw = df.copy()
raw["genres"] = raw["genres"].apply(_load_json_list)
raw["lead_actors"] = raw["cast_names"].apply(_load_json_list)
raw["release_date"] = pd.to_datetime(raw["release_date"], errors="coerce")

print("Rows:", len(raw))
print("Revenue: min=${:,} max=${:,} mean=${:,}".format(
    int(raw["revenue"].min()), int(raw["revenue"].max()), int(raw["revenue"].mean())))"""
)

md(
    """## 2. Train / validation / test split

Stratified by **revenue quartile** so the expensive movies are well represented in
every split. 70 / 15 / 15, deterministic via `seed=42`."""
)
code(
    """TEST_SPLIT = settings.TEST_SPLIT  # 0.15
SEED = 42

def split_quartile(raw, test_frac, seed):
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
        val_idx.extend(group_idx[n_test:n_test + n_val])
        train_idx.extend(group_idx[n_test + n_val:])
    rng.shuffle(train_idx)
    return raw.loc[train_idx], raw.loc[val_idx], raw.loc[test_idx]

train_raw, val_raw, test_raw = split_quartile(raw, TEST_SPLIT, SEED)
print(f"train={len(train_raw)}  validation={len(val_raw)}  test={len(test_raw)}")

y_train = np.log1p(train_raw["revenue"].astype(float).to_numpy())
y_val   = np.log1p(val_raw["revenue"].astype(float).to_numpy())
y_test  = np.log1p(test_raw["revenue"].astype(float).to_numpy())"""
)

md(
    """## 3. Feature engineering + scaling (fit on train ONLY)

`RevenuePreprocessor.fit` computes genre flags, frequency-based "track record"
features, log transforms and a `StandardScaler`. Fitting it **only on the training
split** prevents any information about the validation/test revenue from leaking in."""
)
code(
    """from app.ml.preprocessor import RevenuePreprocessor

preprocessor = RevenuePreprocessor.fit(train_raw)
x_train = preprocessor.predict_features(train_raw)
x_val   = preprocessor.predict_features(val_raw)
x_test  = preprocessor.predict_features(test_raw)

print("Features:", len(preprocessor.feature_columns))
print("Numerical:", len(preprocessor.numeric_columns), "| Genre flags:", len(preprocessor.genre_columns))
print("Input shape:", x_train.shape)"""
)

md(
    """## 4. Build & train the DNN

Hyper-parameters come from `training.model` (already tuned — see
`backend/models/evaluation/tuning_results.csv`). The model uses **Huber loss**
(delta=1) + **L2** regularization, which makes it robust to the extreme-revenue
outliers in box-office data. Training uses:
- **EarlyStopping** (patience 25, restores best weights)
- **ReduceLROnPlateau** (factor 0.5, patience 8)
- **ModelCheckpoint** (saves the best `.keras` on validation loss)"""
)
code(
    r"""from training.model import (
    DEFAULT_UNITS, DEFAULT_DROPOUTS, DEFAULT_BATCH_NORM, DEFAULT_L2,
    describe_architecture, train_dnn,
)

print("\n".join(describe_architecture()))"""
)
code(
    """EPOCHS = settings.EPOCHS        # 300
BATCH_SIZE = settings.BATCH_SIZE  # 128
LEARNING_RATE = settings.LEARNING_RATE  # 1e-3

model_path = str(Path(settings.MODEL_PATH))
model, history = train_dnn(
    x_train, y_train, x_val, y_val,
    input_dim=x_train.shape[1],
    learning_rate=LEARNING_RATE,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    seed=SEED,
    model_path=model_path,
    verbose=1,
    units=DEFAULT_UNITS,
    dropouts=DEFAULT_DROPOUTS,
    batch_norm=DEFAULT_BATCH_NORM,
    l2=DEFAULT_L2,
)
print("Training done. Model saved to", model_path)"""
)

md(
    """## 5. Baseline models

Train a suite of classical ML models on the **same** engineered features for a
fair apples-to-apples comparison. XGBoost is included if installed."""
)
code(
    """from sklearn.ensemble import (AdaBoostRegressor, ExtraTreesRegressor,
                                GradientBoostingRegressor, RandomForestRegressor)
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor

baselines = {
    "Linear Regression": LinearRegression(),
    "Random Forest": RandomForestRegressor(n_estimators=250, max_depth=18, n_jobs=-1, random_state=SEED),
    "Gradient Boosting": GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.06, random_state=SEED),
    "K-Nearest Neighbors": KNeighborsRegressor(n_neighbors=12, weights="distance", n_jobs=-1),
    "Decision Tree": DecisionTreeRegressor(max_depth=14, random_state=SEED),
    "Extra Trees": ExtraTreesRegressor(n_estimators=250, max_depth=20, n_jobs=-1, random_state=SEED),
    "AdaBoost": AdaBoostRegressor(n_estimators=150, learning_rate=0.05, random_state=SEED),
}
try:
    from xgboost import XGBRegressor
    baselines["XGBoost"] = XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.06, random_state=SEED, verbosity=0)
    print("XGBoost available")
except ImportError:
    print("XGBoost not installed - skipping")

baseline_preds = {}
for name, est in baselines.items():
    est.fit(x_train, y_train)
    baseline_preds[name] = est.predict(x_test)
    print(f"  trained {name}")"""
)

md(
    """## 6. Evaluate on the held-out test set

Metrics are reported in **log1p(revenue)** space *and* converted back to **USD**
for readability. R²(log) is the headline number used throughout the API."""
)
code(
    """from training.evaluate import regression_metrics, permutation_importance

dnn_pred = model.predict(x_test, verbose=0).ravel()
dnn_metrics = regression_metrics(y_test, dnn_pred)
print("DNN:", dnn_metrics)

comparison = [{"model": "Deep Neural Network", **dnn_metrics}]
for name, preds in baseline_preds.items():
    m = regression_metrics(y_test, preds)
    comparison.append({"model": name, **m})

import pandas as pd
pd.DataFrame(comparison)[["model", "r2_log", "mae_log", "rmse_log", "mae_revenue", "mape_pct"]].sort_values("r2_log", ascending=False)"""
)
code(
    """importance = permutation_importance(model, x_test, y_test,
                                       preprocessor.feature_columns,
                                       n_repeats=5, seed=SEED)
pd.DataFrame(importance).head(12)"""
)

md(
    """## 7. Persist metrics into the preprocessor

The API uses these to build **expected-range** and **confidence** bands around a
prediction, so we store them on the pickled preprocessor."""
)
code(
    """preprocessor.rmse_log = dnn_metrics["rmse_log"]
preprocessor.mae_log = dnn_metrics["mae_log"]
preprocessor.r2 = dnn_metrics["r2_log"]
print("Preprocessor metric fields set: rmse_log, mae_log, r2")"""
)

md(
    """## 8. Save all production artifacts

This is the step the API vendor app deploys from: model, preprocessor and the
three JSON metadata files."""
)
code(
    """import joblib
from training.evaluate import save_history_json, save_plots

# Preprocessor
Path(settings.PREPROCESSOR_PATH).parent.mkdir(parents=True, exist_ok=True)
joblib.dump(preprocessor, settings.PREPROCESSOR_PATH)
print("Saved preprocessor ->", settings.PREPROCESSOR_PATH)

# Model (ModelCheckpoint already wrote the best; ensure it exists)
if not Path(model_path).exists():
    model.save(model_path)
print("Saved model ->", model_path)

# Training history + plots
Path(settings.EVALUATION_DIR).mkdir(parents=True, exist_ok=True)
save_history_json(history, Path(settings.TRAINING_HISTORY_PATH))
save_plots(y_test, dnn_pred, history.history, comparison, Path(settings.EVALUATION_DIR))
print("Saved training history + plots ->", settings.EVALUATION_DIR)"""
)
code(
    """# feature_config.json
feature_config = {
    "description": "Features available to the DNN. All are knowable before/around release.",
    "target": "revenue", "target_transformation": "log1p", "target_inverse": "expm1",
    "numeric_features": preprocessor.numeric_columns,
    "genre_features": preprocessor.genre_columns,
    "feature_columns": preprocessor.feature_columns,
    "engineered_features": [
        {"name": "budget_log", "description": "log1p(production budget USD)"},
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
print("Saved feature_config.json")"""
)
code(
    """# metrics.json
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
        "layers": describe_architecture(units=DEFAULT_UNITS, dropouts=DEFAULT_DROPOUTS, batch_norm=DEFAULT_BATCH_NORM, l2=DEFAULT_L2),
        "optimizer": f"Adam (lr {LEARNING_RATE}, ReduceLROnPlateau on plateau)",
        "loss": "Huber (delta=1.0)", "metric": "MAE", "l2": DEFAULT_L2,
    },
    "hyperparameter_tuning": {
        "note": "Results in models/evaluation/tuning_results.{csv,json,png}",
        "best_config": {
            "units": list(DEFAULT_UNITS), "dropouts": list(DEFAULT_DROPOUTS),
            "batch_norm": list(DEFAULT_BATCH_NORM), "learning_rate": LEARNING_RATE, "l2": DEFAULT_L2,
        },
    },
}
Path(settings.METRICS_PATH).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
print("Saved metrics.json")"""
)
code(
    """# model_metadata.json
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
    "python_version": platform.python_version(),
    "framework": "TensorFlow / Keras",
    "metrics": dnn_metrics,
    "training_hyperparameters": {
        "epochs": EPOCHS, "batch_size": BATCH_SIZE, "learning_rate": LEARNING_RATE,
        "seed": SEED, "early_stopping_patience": 25, "reduce_lr_patience": 8,
    },
}
Path(settings.METADATA_PATH).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
print("Saved model_metadata.json")"""
)

md(
    """## 9. Convert to LiteRT for serving

The production API serves a **0.77 MB** `.tflite` model via `ai-edge-litert`
instead of the ~600 MB TensorFlow wheel (this is what keeps Vercel/Render bundles
small and cold starts fast). Run the converter after retraining and commit the
`.tflite` to git.

```python
# from the repo root
& "backend\\.venv\\Scripts\\python.exe" backend\\scripts\\convert_to_tflite.py
```
> The converter validates numerical **parity** (well under 0.5%) between the
> `.keras` and `.tflite` copies before it exits 0."""
)

md("""## 10. Summary

| Model | R² (log) | MAE (USD) | Notes |
|---|---|---|---|
| Deep Neural Network | see output above | see above | **production model** |

Prediction examples validated in `scripts/fresh_load.py`, and the live API is
served from the committed artifacts. After retraining, **commit the regenerated
`backend/models/*` files** so Render/Vercel pick up the new weights on redeploy.""")

nb.cells = cells
OUT.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, OUT)
print(f"Wrote {OUT} with {len(cells)} cells")
