"""Business logic for single and batch revenue prediction."""

from __future__ import annotations

import math
from datetime import date

import numpy as np
import pandas as pd

from ..config import settings
from ..ml.performance import classify_performance
from ..schemas.predict import (
    BatchPredictItem,
    BatchPredictResponse,
    BatchRowResult,
    PredictRequest,
    PredictResponse,
)
from ..utils.errors import InvalidInputError
from ..utils.formatting import format_crore, format_million, format_usd
from .model_service import DISCLAIMER, ModelService, get_model_service

# 95% coverage factor around the held-out test residual (log space).
RANGE_Z = 1.96
# Confidence heuristic weights (documented in README).
R2_WEIGHT = 0.55
KNOWN_FEATURE_WEIGHT = 0.45


def _build_raw_row(payload: PredictRequest | BatchPredictItem) -> dict:
    """Map a validated API payload to the raw row dict the preprocessor expects."""
    year = payload.release_year or date.today().year
    month = payload.release_month
    day = max(1, min(28, payload.release_day))  # never allow an invalid date
    release_date = f"{year:04d}-{month:02d}-{day:02d}"
    return {
        "budget": float(payload.budget),
        "runtime": float(payload.runtime),
        "genres": payload.genres,
        "release_date": release_date,
        "popularity": float(payload.popularity),
        "vote_average": float(payload.rating),
        "vote_count": float(payload.vote_count),
        "original_language": payload.language or "en",
        "production_company": payload.production_company,
        "director": payload.director,
        "lead_actors": payload.lead_actors,
    }


class PredictionService:
    def __init__(self, model_service: ModelService | None = None) -> None:
        self._model = model_service or get_model_service()

    # ------------------------------------------------------------ helpers ----
    def _expected_range(self, pred_log: float) -> dict:
        rmse_log = self._model.preprocessor.rmse_log or 0.6
        lower_log = pred_log - RANGE_Z * rmse_log
        upper_log = pred_log + RANGE_Z * rmse_log
        lower = self._model.preprocessor.inverse_log1p(lower_log)
        upper = self._model.preprocessor.inverse_log1p(upper_log)
        return {
            "lower": round(lower, 2),
            "upper": round(upper, 2),
            "method": (
                "95% band from held-out test residual spread (log1p space), "
                "inverted via expm1"
            ),
        }

    def _confidence(self, raw_row: dict, pred_log: float) -> float:
        """Heuristic 0-100 confidence score (NOT a probability)."""
        r2 = self._model.preprocessor.r2 or 0.0
        r2_score = max(0.0, min(1.0, r2))

        # Penalize inputs that are dominated by unknown identities.
        known_company = 1.0 if raw_row.get("production_company") else 0.0
        known_director = 1.0 if raw_row.get("director") else 0.0
        has_actors = 1.0 if raw_row.get("lead_actors") else 0.0
        has_rating = 1.0 if raw_row.get("vote_average") else 0.0
        known_fraction = (known_company + known_director + has_actors + has_rating) / 4.0

        score = 100.0 * (R2_WEIGHT * r2_score + KNOWN_FEATURE_WEIGHT * known_fraction)
        return round(max(0.0, min(100.0, score)), 1)

    # ------------------------------------------------------------- single ----
    def predict(self, payload: PredictRequest) -> PredictResponse:
        raw_row = _build_raw_row(payload)
        df = pd.DataFrame([raw_row])
        log_pred = self._model.predict_log(df)[0]
        revenue = self._model.preprocessor.inverse_log1p(log_pred)

        contributions = self._model.explain(raw_row)
        expected_range = self._expected_range(log_pred)
        confidence = self._confidence(raw_row, log_pred)
        category = classify_performance(revenue, payload.budget, settings.PERFORMANCE_THRESHOLDS)

        ratio = revenue / payload.budget if payload.budget > 0 else 0.0

        return PredictResponse(
            predicted_revenue=round(revenue, 2),
            predicted_revenue_usd=format_usd(revenue),
            predicted_revenue_million=format_million(revenue),
            predicted_revenue_crore=format_crore(revenue),
            performance_category=category,
            budget=payload.budget,
            revenue_budget_ratio=round(ratio, 2),
            confidence_score=confidence,
            expected_range=expected_range,
            model_version=self._model.model_version,
            contributions=contributions,
            disclaimer=DISCLAIMER,
        )

    def predict_batch(self, items: list[BatchPredictItem]) -> BatchPredictResponse:
        rows: list[dict] = [_build_raw_row(item) for item in items]
        df = pd.DataFrame(rows)
        log_preds = self._model.predict_log(df)

        results: list[BatchRowResult] = []
        success_count = 0
        summaries = []
        for i, (item, log_pred) in enumerate(zip(items, log_preds, strict=True)):
            revenue = self._model.preprocessor.inverse_log1p(float(log_pred))
            category = classify_performance(revenue, item.budget, settings.PERFORMANCE_THRESHOLDS)
            results.append(
                BatchRowResult(
                    row=i + 1,
                    title=item.title,
                    status="success",
                    predicted_revenue=round(revenue, 2),
                    predicted_revenue_usd=format_usd(revenue),
                    performance_category=category,
                )
            )
            success_count += 1
            summaries.append(revenue)

        return BatchPredictResponse(
            total_rows=len(items),
            successful=success_count,
            failed=len(items) - success_count,
            results=results,
            summary=None,
        )

    def predict_csv(self, df: pd.DataFrame) -> BatchPredictResponse:
        """Predict from a user-uploaded CSV DataFrame (documented schema)."""
        required = {"title", "budget", "runtime"}
        missing = required - set(df.columns)
        if missing:
            raise InvalidInputError(
                "CSV is missing required columns: " + ", ".join(sorted(missing)) +
                ". Expected: title, budget, runtime, genres, release_month, release_day, "
                "release_year, production_company, director, lead_actors, rating, "
                "vote_count, popularity, language."
            )

        items: list[BatchPredictItem] = []
        errors: list[BatchRowResult] = []
        for i, row in df.iterrows():
            try:
                items.append(_csv_row_to_item(i + 1, row))
            except ValueError as exc:
                title = str(row.get("title") or "").strip() or None
                errors.append(
                    BatchRowResult(row=i + 1, title=title, status="error", error=f"Invalid row: {exc}")
                )
        if items:
            batch = self.predict_batch(items)
            results = errors + batch.results
            results.sort(key=lambda r: r.row)
            return BatchPredictResponse(
                total_rows=len(errors) + batch.successful + batch.failed,
                successful=batch.successful,
                failed=len(errors) + batch.failed,
                results=results,
                summary=None,
            )
        return BatchPredictResponse(
            total_rows=len(errors), successful=0, failed=len(errors), results=errors, summary=None
        )


def _csv_row_to_item(row_number: int, row: pd.Series) -> BatchPredictItem:
    """Parse a CSV row into a validated batch item with readable errors."""
    def _text(col: str) -> str | None:
        val = row.get(col)
        if val is None:
            return None
        if isinstance(val, float) and math.isnan(val):
            return None
        s = str(val).strip()
        return s or None

    def _float(col: str) -> float:
        val = _text(col)
        if val is None:
            raise ValueError(f"`{col}` is missing.")
        try:
            return float(val)
        except ValueError as exc:
            raise ValueError(f"`{col}` is not a number: {val!r}") from exc

    def _int(col: str, default: int | None = None) -> int | None:
        val = _text(col)
        if val is None:
            return default
        try:
            return int(float(val))
        except ValueError as exc:
            raise ValueError(f"`{col}` is not an integer: {val!r}") from exc

    budget = _float("budget")
    if budget <= 0:
        raise ValueError("`budget` must be greater than zero.")
    runtime = _float("runtime")
    if runtime <= 0:
        raise ValueError("`runtime` must be greater than zero.")

    genres_raw = _text("genres")
    genres = []
    if genres_raw:
        genres = [g.strip() for g in genres_raw.split("|") if g.strip()]

    actors_raw = _text("lead_actors")
    lead_actors = []
    if actors_raw:
        lead_actors = [a.strip() for a in actors_raw.split("|") if a.strip()]

    return BatchPredictItem(
        title=_text("title") or f"Movie {row_number}",
        budget=budget,
        runtime=runtime,
        genres=genres,
        release_month=_int("release_month", 1) or 1,
        release_day=_int("release_day", 15) or 15,
        release_year=_int("release_year"),
        production_company=_text("production_company"),
        director=_text("director"),
        lead_actors=lead_actors,
        rating=_float("rating") if _text("rating") is not None else 5.0,
        vote_count=_int("vote_count", 0) or 0,
        popularity=_float("popularity") if _text("popularity") is not None else 0.0,
        language=_text("language") or "en",
    )
