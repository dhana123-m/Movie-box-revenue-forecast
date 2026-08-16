"""Evaluation: metrics, plots and JSON artifacts for the DNN + baselines."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score  # noqa: E402

logger = logging.getLogger(__name__)


def regression_metrics(y_true, y_pred):
    """Compute MAE / RMSE / R² / MAPE. ``y`` are log1p-transformed values."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))

    # Metrics in the original revenue space (reverse the log transform).
    rev_true = np.expm1(y_true)
    rev_pred = np.clip(np.expm1(y_pred), a_min=0.0, a_max=None)
    mae_rev = float(mean_absolute_error(rev_true, rev_pred))
    rmse_rev = float(np.sqrt(mean_squared_error(rev_true, rev_pred)))
    r2_rev = float(r2_score(rev_true, rev_pred))

    # MAPE only where mathematically meaningful (all revenues > 0 in this dataset).
    mape = float(np.mean(np.abs((rev_true - rev_pred) / rev_true)) * 100.0)

    return {
        "mae_log": round(mae, 4),
        "rmse_log": round(rmse, 4),
        "r2_log": round(r2, 4),
        "mae_revenue": round(mae_rev, 2),
        "rmse_revenue": round(rmse_rev, 2),
        "r2_revenue": round(r2_rev, 4),
        "mape_pct": round(mape, 2),
    }


def permutation_importance(model, x_test, y_test, feature_names, n_repeats: int = 5, seed: int = 42):
    """Feature importance by shuffling (model-agnostic, on the test split)."""
    rng = np.random.default_rng(seed)
    base_pred = model.predict(x_test, verbose=0).ravel()
    base_mae = float(mean_absolute_error(y_test, base_pred))

    scores = {}
    for i, name in enumerate(feature_names):
        losses = []
        for _ in range(n_repeats):
            x_pert = x_test.copy()
            perm = rng.permutation(x_pert.shape[0])
            x_pert[:, i] = x_pert[perm, i]
            pred = model.predict(x_pert, verbose=0).ravel()
            losses.append(float(mean_absolute_error(y_test, pred)))
        scores[name] = float(np.mean(losses) - base_mae)

    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [{"feature": name, "importance": round(value, 5)} for name, value in ordered]


def save_plots(
    y_test,
    y_pred,
    history,
    comparison: list[dict],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    y_test = np.asarray(y_test, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    rev_test = np.expm1(y_test)
    rev_pred = np.clip(np.expm1(y_pred), a_min=0.0, a_max=None)
    palette = ["#8b5cf6", "#6366f1", "#22d3ee"]

    # 1. Actual vs predicted
    fig, ax = plt.subplots(figsize=(6, 5), dpi=110)
    ax.scatter(rev_test, rev_pred, s=14, alpha=0.5, color=palette[0])
    lo = min(rev_test.min(), rev_pred.min())
    hi = max(rev_test.max(), rev_pred.max())
    ax.plot([lo, hi], [lo, hi], color="#fbbf24", ls="--", lw=1.4, label="Ideal")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Actual Revenue ($)"); ax.set_ylabel("Predicted Revenue ($)")
    ax.set_title("DNN — Actual vs Predicted Revenue (test set)")
    ax.legend()
    fig.tight_layout(); fig.savefig(output_dir / "actual_vs_predicted.png"); plt.close(fig)

    # 2. Training curves
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), dpi=110)
    for ax, key, title in (
        (axes[0], "loss", "Loss (MSE, log1p revenue)"),
        (axes[1], "mae", "Mean Absolute Error (log1p revenue)"),
    ):
        ax.plot(history[key], label="train", color=palette[0])
        if f"val_{key}" in history:
            ax.plot(history[f"val_{key}"], label="validation", color=palette[2])
        ax.set_xlabel("Epoch"); ax.set_title(title); ax.legend()
    fig.tight_layout(); fig.savefig(output_dir / "training_curves.png"); plt.close(fig)

    # 3. Residuals
    residuals = y_test - y_pred
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=110)
    ax.scatter(y_pred, residuals, s=14, alpha=0.5, color=palette[1])
    ax.axhline(0, color="#fbbf24", ls="--", lw=1.2)
    ax.set_xlabel("Predicted (log1p revenue)"); ax.set_ylabel("Residual (log1p revenue)")
    ax.set_title("DNN — Residual Plot (test set)")
    fig.tight_layout(); fig.savefig(output_dir / "residuals.png"); plt.close(fig)

    # 4. Model comparison
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=110)
    names = [c["model"] for c in comparison]
    r2s = [c["r2_log"] for c in comparison]
    colors = [palette[2] if n == "DNN" else "#64748b" for n in names]
    bars = ax.bar(names, r2s, color=colors, edgecolor="none")
    for bar, value in zip(bars, r2s, strict=False):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.005, f"{value:.3f}", ha="center", fontsize=8)
    ax.set_ylabel("R² (log1p revenue)"); ax.set_title("Model Comparison — Test Set")
    ax.set_ylim(0, max(1.0, max(r2s) * 1.1))
    fig.autofmt_xdate()
    fig.tight_layout(); fig.savefig(output_dir / "model_comparison.png"); plt.close(fig)

    # 5. Error distribution
    rel_err = (rev_pred - rev_test) / rev_test * 100.0
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=110)
    ax.hist(rel_err, bins=60, color=palette[0], alpha=0.85, edgecolor="none")
    ax.axvline(0, color="#fbbf24", ls="--", lw=1.2)
    ax.set_xlabel("Prediction Error (%)"); ax.set_ylabel("Frequency")
    ax.set_title("DNN — Prediction Error Distribution (test set)")
    fig.tight_layout(); fig.savefig(output_dir / "error_distribution.png"); plt.close(fig)

    logger.info("Saved evaluation plots to %s", output_dir)


def save_history_json(history, path: Path) -> None:
    trimmed = {
        "epochs": int(history.epoch[-1]) + 1,
        "loss": [float(v) for v in history.history.get("loss", [])],
        "val_loss": [float(v) for v in history.history.get("val_loss", [])],
        "mae": [float(v) for v in history.history.get("mae", [])],
        "val_mae": [float(v) for v in history.history.get("val_mae", [])],
    }
    path.write_text(json.dumps(trimmed, indent=2), encoding="utf-8")
