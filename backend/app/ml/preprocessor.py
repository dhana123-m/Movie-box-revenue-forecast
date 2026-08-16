"""Shared preprocessing + feature-engineering pipeline.

One object of this class is fitted on the *training split only* and pickled to
``backend/models/preprocessor.pkl``. The same object is used:

* during training to transform the validation/test splits, and
* at prediction time by the API to turn a raw movie payload into the exact
  numeric feature vector consumed by the DNN.

Feature engineering notes
-------------------------
* ``budget`` and ``vote_count`` are log1p transformed (heavy-tailed).
* ``release_*`` features are derived from the release date.
* ``*_frequency`` features are counts of how many times a director, production
  company or lead actor appears in the training set. They are *identity*
  counts (not revenue-derived), so they do not leak the target, and they are
  a defensible proxy for "track record" that is available before release.
* Genres are multi-hot encoded over the most frequent genres in training.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


class RevenuePreprocessor:
    def __init__(
        self,
        feature_columns: list[str],
        numeric_columns: list[str],
        genre_columns: list[str],
        scaler: StandardScaler,
        company_freq: dict[str, int],
        director_freq: dict[str, int],
        actor_freq: dict[str, int],
        feature_std: dict[str, float],
        rmse_log: float,
        mae_log: float,
        r2: float,
    ) -> None:
        self.feature_columns = feature_columns
        self.numeric_columns = numeric_columns
        self.genre_columns = genre_columns
        self.scaler = scaler
        self.company_freq = company_freq
        self.director_freq = director_freq
        self.actor_freq = actor_freq
        self.feature_std = feature_std
        self.rmse_log = rmse_log
        self.mae_log = mae_log
        self.r2 = r2

    # ------------------------------------------------------------------ fit --
    @classmethod
    def fit(
        cls,
        df_train: pd.DataFrame,
    ) -> "RevenuePreprocessor":
        """Fit the pipeline on the training split only.

        ``df_train`` must contain the raw columns listed in ``RAW_COLUMNS``.
        """
        genre_columns = _top_genres(df_train, n=18)
        company_freq = _value_counts(df_train, "production_company")
        director_freq = _value_counts(df_train, "director")
        actor_freq = _actor_frequencies(df_train)

        feature_columns = ENGINEERED_FEATURES + genre_columns
        numeric_columns = list(feature_columns)  # every feature is scaled

        features = cls._engineer(df_train, genre_columns, company_freq, director_freq, actor_freq)
        scaler = StandardScaler()
        scaler.fit(features[numeric_columns].to_numpy(dtype="float64"))

        feature_std = {}
        for col in numeric_columns:
            feature_std[col] = float(features[col].std(ddof=0))

        return cls(
            feature_columns=feature_columns,
            numeric_columns=numeric_columns,
            genre_columns=genre_columns,
            scaler=scaler,
            company_freq=company_freq,
            director_freq=director_freq,
            actor_freq=actor_freq,
            feature_std=feature_std,
            rmse_log=0.0,
            mae_log=0.0,
            r2=0.0,
        )

    # ------------------------------------------------------ engineering ------
    def engineer(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer the raw feature matrix (unscaled) from raw movie rows."""
        return self._engineer(
            df,
            self.genre_columns,
            self.company_freq,
            self.director_freq,
            self.actor_freq,
        )

    @staticmethod
    def _engineer(
        df: pd.DataFrame,
        genre_columns: list[str],
        company_freq: dict[str, int],
        director_freq: dict[str, int],
        actor_freq: dict[str, int],
    ) -> pd.DataFrame:
        out = pd.DataFrame(index=df.index)
        budget = df["budget"].astype(float).clip(lower=0.0)
        runtime = df["runtime"].astype(float).clip(lower=1.0)
        vote_count = df["vote_count"].astype(float).clip(lower=0.0)

        out["budget_log"] = np.log1p(budget)
        out["budget_per_runtime"] = budget / runtime
        out["runtime"] = runtime
        out["popularity"] = df["popularity"].astype(float)
        out["vote_average"] = df["vote_average"].astype(float)
        out["vote_count_log"] = np.log1p(vote_count)

        release = pd.to_datetime(df["release_date"], errors="coerce")
        out["release_year"] = release.dt.year.fillna(2000).astype(int)
        out["release_month"] = release.dt.month.fillna(6).astype(int)
        out["release_quarter"] = ((out["release_month"] - 1) // 3 + 1).astype(int)
        out["release_weekday"] = release.dt.dayofweek.fillna(3).astype(int)

        out["genre_count"] = df["genres"].apply(lambda g: len(g) if isinstance(g, list) else 0)

        lead_actors = df["lead_actors"]
        out["cast_size"] = lead_actors.apply(lambda a: len(a) if isinstance(a, list) else 0)

        def _star_power(actors: Any) -> int:
            if not isinstance(actors, list) or not actors:
                return 0
            return max((actor_freq.get(str(a), 0) for a in actors[:5]), default=0)

        out["cast_star_power"] = lead_actors.apply(_star_power)
        out["director_frequency"] = df["director"].map(lambda d: director_freq.get(str(d), 0) if d else 0)
        out["company_frequency"] = df["production_company"].map(
            lambda c: company_freq.get(str(c), 0) if c else 0
        )
        out["language_is_en"] = df["original_language"].map(
            lambda l: 1 if str(l).lower() == "en" else 0
        )

        for genre in genre_columns:
            out[genre] = df["genres"].apply(lambda g: 1 if isinstance(g, list) and genre in g else 0)

        return out

    # ------------------------------------------------------------ scaling -----
    def transform(self, features: pd.DataFrame) -> np.ndarray:
        """Return the scaled feature matrix in the canonical column order."""
        scaled = self.scaler.transform(features[self.numeric_columns].to_numpy(dtype="float64"))
        frame = features[self.feature_columns].copy()
        frame[self.numeric_columns] = scaled
        return frame[self.feature_columns].to_numpy(dtype="float32")

    def predict_features(self, df: pd.DataFrame) -> np.ndarray:
        return self.transform(self.engineer(df))

    # -------------------------------------------------------------- target ----
    @staticmethod
    def inverse_log1p(values: np.ndarray | float) -> float:
        return float(np.clip(np.expm1(values), a_min=0.0, a_max=None))


# Raw columns expected in any DataFrame passed to ``engineer`` / ``fit``.
RAW_COLUMNS = [
    "budget",
    "runtime",
    "genres",
    "release_date",
    "popularity",
    "vote_average",
    "vote_count",
    "original_language",
    "production_company",
    "director",
    "lead_actors",
]

ENGINEERED_FEATURES = [
    "budget_log",
    "budget_per_runtime",
    "runtime",
    "popularity",
    "vote_average",
    "vote_count_log",
    "release_year",
    "release_month",
    "release_quarter",
    "release_weekday",
    "genre_count",
    "cast_size",
    "cast_star_power",
    "director_frequency",
    "company_frequency",
    "language_is_en",
]


def _top_genres(df: pd.DataFrame, n: int = 18) -> list[str]:
    counts: dict[str, int] = {}
    for genres in df["genres"]:
        if isinstance(genres, list):
            for g in genres:
                counts[g] = counts.get(g, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [name for name, _ in ordered[:n]]


def _value_counts(df: pd.DataFrame, column: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in df[column]:
        if value:
            key = str(value)
            counts[key] = counts.get(key, 0) + 1
    return counts


def _actor_frequencies(df: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = {}
    for actors in df["lead_actors"]:
        if isinstance(actors, list):
            for actor in actors:
                key = str(actor)
                counts[key] = counts.get(key, 0) + 1
    return counts
