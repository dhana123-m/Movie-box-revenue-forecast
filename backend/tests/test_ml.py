"""Tests for the ML building blocks (genres, classification, preprocessor)."""

import numpy as np
import pandas as pd

from app.config import settings
from app.ml.genres import GENRE_NAMES
from app.ml.performance import classify_performance, performance_labels


def test_genre_vocabulary_is_sane():
    assert "Action" in GENRE_NAMES
    assert "Drama" in GENRE_NAMES
    assert "Science Fiction" in GENRE_NAMES
    assert len(GENRE_NAMES) == len(set(GENRE_NAMES))


def test_performance_labels_ordered():
    labels = performance_labels(settings.PERFORMANCE_THRESHOLDS)
    assert labels == ["FLOP", "AVERAGE", "HIT", "SUPER_HIT", "BLOCKBUSTER"]


def test_classify_performance_thresholds():
    t = settings.PERFORMANCE_THRESHOLDS
    budget = 100.0
    cases = [
        (50.0, "FLOP"),
        (150.0, "AVERAGE"),
        (300.0, "HIT"),
        (600.0, "SUPER_HIT"),
        (900.0, "BLOCKBUSTER"),
    ]
    for revenue, expected in cases:
        assert classify_performance(revenue, budget, t) == expected


def test_classify_handles_zero_budget():
    assert classify_performance(500.0, 0, settings.PERFORMANCE_THRESHOLDS) == "BLOCKBUSTER"


def test_preprocessor_inverse_roundtrip(model_service):
    pre = model_service.preprocessor
    values = np.array([0.0, 5.0, 12.0, 20.0])
    inv = np.array([pre.inverse_log1p(float(v)) for v in values])
    np.testing.assert_allclose(inv, np.expm1(values), rtol=1e-6)
    assert inv.min() >= 0.0


def test_preprocessor_predict_features_shape(model_service):
    pre = model_service.preprocessor
    row = pd.DataFrame(
        [
            {
                "budget": 1e8,
                "runtime": 120,
                "genres": ["Action", "Drama"],
                "release_date": "2026-07-18",
                "popularity": 50.0,
                "vote_average": 7.0,
                "vote_count": 10000,
                "original_language": "en",
                "production_company": "Warner Bros.",
                "director": "Christopher Nolan",
                "lead_actors": ["Actor A", "Actor B"],
            }
        ]
    )
    vec = pre.predict_features(row)
    assert vec.shape == (1, len(pre.feature_columns))
    assert vec.shape[1] == 34
