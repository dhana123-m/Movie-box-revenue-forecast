"""Hyper-parameter search for the revenue DNN.

Runs a bounded grid/random sweep over units, dropout, L2 and learning rate,
training each config with the same early-stopping discipline as the production
pipeline. Reports validation MAE per trial and persists:

    backend/models/evaluation/tuning_results.csv
    backend/models/evaluation/tuning_results.json
    backend/models/evaluation/tuning_results.png

Run from the backend directory:

    python training/hyperparameter_tuning.py
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from tensorflow import keras  # noqa: E402

from app.config import settings  # noqa: E402
from app.ml.preprocessor import RevenuePreprocessor  # noqa: E402
from training.model import DEFAULT_UNITS, DEFAULT_DROPOUTS, DEFAULT_BATCH_NORM, train_dnn  # noqa: E402
from training.train import _load_dataset, _raw_frame, _split  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("tune")

SEED = 42
TRIAL_EPOCHS = 80
TRIAL_PATIENCE = 10
TRIAL_BATCH_SIZE = 64

# (units, dropouts, batch_norm, learning_rate, l2)
GRID = [
    # baseline (production default)
    ((256, 128, 64, 32), (0.30, 0.25, 0.20, 0.20), (True, True, False, True), 1e-3, 1e-4),
    # width
    ((512, 256, 128, 64), (0.35, 0.30, 0.25, 0.20), (True, True, True, True), 1e-3, 1e-4),
    ((192, 128, 64, 32), (0.30, 0.25, 0.20, 0.20), (True, True, True, True), 1e-3, 1e-4),
    # depth
    ((256, 128, 64), (0.30, 0.25, 0.20), (True, True, True), 1e-3, 1e-4),
    ((256, 192, 128, 64, 32), (0.30, 0.25, 0.20, 0.15, 0.15), (True, True, True, True, True), 1e-3, 1e-4),
    # dropout strength
    ((256, 128, 64, 32), (0.20, 0.20, 0.15, 0.15), (True, True, True, True), 1e-3, 1e-4),
    ((256, 128, 64, 32), (0.40, 0.35, 0.30, 0.25), (True, True, True, True), 1e-3, 1e-4),
    # learning rate
    ((256, 128, 64, 32), (0.30, 0.25, 0.20, 0.20), (True, True, True, True), 3e-3, 1e-4),
    ((256, 128, 64, 32), (0.30, 0.25, 0.20, 0.20), (True, True, True, True), 5e-4, 1e-4),
    # L2 strength
    ((256, 128, 64, 32), (0.30, 0.25, 0.20, 0.20), (True, True, True, True), 1e-3, 1e-5),
    ((256, 128, 64, 32), (0.30, 0.25, 0.20, 0.20), (True, True, True, True), 1e-3, 3e-4),
]


def _best_val_mae(history) -> float:
    values = history.history.get("val_mae", [])
    return float(min(values)) if values else float("nan")


def _run_trial(x_train, y_train, x_val, y_val, config, seed: int) -> dict:
    units, dropouts, batch_norm, lr, l2 = config
    start = time.perf_counter()
    model, history = train_dnn(
        x_train, y_train, x_val, y_val,
        input_dim=x_train.shape[1],
        learning_rate=lr,
        epochs=TRIAL_EPOCHS,
        batch_size=TRIAL_BATCH_SIZE,
        seed=seed,
        verbose=0,
        units=units,
        dropouts=dropouts,
        batch_norm=batch_norm,
        l2=l2,
    )
    keras.backend.clear_session()
    return {
        "units": "/".join(map(str, units)),
        "dropouts": "/".join(f"{d:.2f}" for d in dropouts),
        "batch_norm": "/".join("1" if b else "0" for b in batch_norm),
        "learning_rate": lr,
        "l2": l2,
        "epochs_trained": int(history.epoch[-1]) + 1,
        "best_val_mae": round(_best_val_mae(history), 5),
        "seconds": round(time.perf_counter() - start, 1),
    }


def _save_outputs(results: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(results).sort_values("best_val_mae")

    frame.to_csv(output_dir / "tuning_results.csv", index=False)
    (output_dir / "tuning_results.json").write_text(
        json.dumps(frame.to_dict(orient="records"), indent=2), encoding="utf-8"
    )

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: E402

    fig, ax = plt.subplots(figsize=(11, 5), dpi=110)
    labels = [
        f"{u}\nlr={lr:.0e}·L2={l2:.0e}" for u, _, _, lr, l2 in [r["config"] for r in results]
    ]
    vals = [r["best_val_mae"] for r in results]
    colors = ["#22d3ee" if v == min(vals) else "#64748b" for v in vals]
    bars = ax.bar(range(len(vals)), vals, color=colors, edgecolor="none")
    for bar, v in zip(bars, vals, strict=False):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.002, f"{v:.4f}", ha="center", fontsize=8)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("Best validation MAE (log1p revenue)")
    ax.set_title("Hyper-parameter tuning — DNN validation MAE (lower is better)")
    fig.tight_layout()
    fig.savefig(output_dir / "tuning_results.png")
    plt.close(fig)
    logger.info("Saved tuning results to %s", output_dir)


def main() -> None:
    global TRIAL_EPOCHS

    parser = argparse.ArgumentParser(description="Sweep DNN hyper-parameters on validation MAE.")
    parser.add_argument("--epochs", type=int, default=TRIAL_EPOCHS)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    TRIAL_EPOCHS = args.epochs

    df = _load_dataset()
    raw = _raw_frame(df)
    logger.info("Dataset rows: %d", len(raw))

    train_raw, val_raw, _ = _split(raw, settings.TEST_SPLIT, args.seed)
    y_train = np.log1p(train_raw["revenue"].astype(float).to_numpy())
    y_val = np.log1p(val_raw["revenue"].astype(float).to_numpy())

    preprocessor = RevenuePreprocessor.fit(train_raw)
    x_train = preprocessor.predict_features(train_raw)
    x_val = preprocessor.predict_features(val_raw)

    results = []
    for i, config in enumerate(GRID, start=1):
        logger.info("[%d/%d] trial %s", i, len(GRID), config[0])
        trial = _run_trial(x_train, y_train, x_val, y_val, config, args.seed)
        trial["config"] = config
        results.append(trial)
        logger.info(
            "  -> val MAE=%.5f (epochs=%d, %.1fs)",
            trial["best_val_mae"], trial["epochs_trained"], trial["seconds"],
        )

    ordered = sorted(results, key=lambda r: r["best_val_mae"])
    _save_outputs(ordered, Path(settings.EVALUATION_DIR))

    logger.info("=" * 60)
    logger.info("BEST CONFIG: units=%s lr=%s l2=%s val_MAE=%.5f",
                ordered[0]["config"][0], ordered[0]["config"][3], ordered[0]["config"][4],
                ordered[0]["best_val_mae"])
    logger.info("=" * 60)
    for rank, r in enumerate(ordered, start=1):
        logger.info("%2d. %-24s lr=%-6s l2=%-6s val_MAE=%.5f",
                    rank, r["units"], r["config"][3], r["config"][4], r["best_val_mae"])


if __name__ == "__main__":
    main()
