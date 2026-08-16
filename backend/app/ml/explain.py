"""Prediction-level sensitivity analysis for explainability.

For each numeric input feature we re-predict after nudging the feature by a
small fraction of its observed training standard deviation (±5%). The signed
change in the prediction indicates whether the feature pushes revenue up or
down at the current input point.

This is a gradient-free, model-agnostic sensitivity estimate. It is NOT a
causal claim and NOT a calibrated feature-importance measure.
"""

from __future__ import annotations

import copy

import numpy as np
import pandas as pd

from ..schemas.predict import FeatureContribution

# Human readable labels for the features we can explain.
FEATURE_LABELS: dict[str, str] = {
    "budget_log": "Budget",
    "runtime": "Runtime",
    "popularity": "Popularity",
    "vote_average": "IMDb Rating",
    "vote_count_log": "Vote Count",
    "release_year": "Release Year",
    "release_month": "Release Month",
    "release_quarter": "Release Quarter",
    "release_weekday": "Release Weekday",
    "budget_per_runtime": "Budget per Minute",
    "genre_count": "Number of Genres",
    "cast_size": "Cast Size",
    "cast_star_power": "Cast Star Power",
    "director_frequency": "Director Track Record",
    "company_frequency": "Production Company Track Record",
    "language_is_en": "English Language",
}

NUDGE_FRACTION = 0.05
RELATIVE_DELTA_MIN = 0.005  # ignore changes smaller than 0.5% relative


class SensitivityExplainer:
    """Explains a single prediction by local input perturbation (raw space)."""

    def __init__(self, model, preprocessor) -> None:
        self.model = model
        self.preprocessor = preprocessor

    def explain(self, raw_row: dict) -> list[FeatureContribution]:
        base_df = pd.DataFrame([raw_row])
        base_vec = self.preprocessor.predict_features(base_df)
        base_pred_log = float(self.model.predict(base_vec, verbose=0)[0][0])
        contributions: list[FeatureContribution] = []

        for name in self.preprocessor.feature_columns:
            if name not in self.preprocessor.numeric_columns:
                continue
            raw_key = _raw_key_for(name)
            if raw_key is None or raw_key not in raw_row:
                continue

            span = self.preprocessor.feature_std.get(name, 1.0)
            delta = span * NUDGE_FRACTION
            if delta == 0:
                continue

            perturbed = copy.deepcopy(raw_row)
            value = perturbed.get(raw_key)
            if isinstance(value, (int, float)):
                perturbed[raw_key] = value + delta
                perturbed_df = pd.DataFrame([perturbed])
                vec = self.preprocessor.predict_features(perturbed_df)
                pred_log = float(self.model.predict(vec, verbose=0)[0][0])

                relative_delta = abs(pred_log - base_pred_log)
                if relative_delta < RELATIVE_DELTA_MIN:
                    impact = "neutral"
                elif pred_log > base_pred_log:
                    impact = "positive"
                else:
                    impact = "negative"

                contributions.append(
                    FeatureContribution(
                        feature=name,
                        label=FEATURE_LABELS.get(name, name.replace("_", " ").title()),
                        impact=impact,
                        magnitude=round(float(relative_delta), 4),
                    )
                )

        contributions.sort(key=lambda c: c.magnitude, reverse=True)
        return contributions[:10]


def _raw_key_for(feature: str) -> str | None:
    mapping = {
        "budget_log": "budget",
        "budget_per_runtime": "budget",
        "runtime": "runtime",
        "popularity": "popularity",
        "vote_average": "vote_average",
        "vote_count_log": "vote_count",
        "release_year": "release_year",
        "release_month": "release_month",
        "release_quarter": "release_month",
        "release_weekday": "release_date",
        "genre_count": "genres",
        "cast_size": "lead_actors",
        "cast_star_power": "lead_actors",
        "director_frequency": "director",
        "company_frequency": "production_company",
        "language_is_en": "original_language",
    }
    return mapping.get(feature)
