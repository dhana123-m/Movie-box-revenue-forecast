"""Feature engineering: raw TMDB 5000 CSVs -> cleaned processed dataset.

Documented in the README under "Dataset preprocessing" and "Feature
engineering". The output CSV contains both the fields used to seed the
database/analytics and the raw fields consumed by ``RevenuePreprocessor``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

RAW_COLUMNS = [
    "id",
    "title",
    "budget",
    "revenue",
    "runtime",
    "release_date",
    "release_year",
    "release_month",
    "release_quarter",
    "release_weekday",
    "popularity",
    "vote_average",
    "vote_count",
    "original_language",
    "production_company",
    "director",
    "cast_names",
    "cast_size",
    "genres",
    "primary_genre",
    "is_demo",
    "status",
]

# Validation ranges (documented in README).
RUNTIME_MIN = 30
RUNTIME_MAX = 400
YEAR_MIN = 1960
YEAR_MAX = 2100
TOP_CAST = 10


def _parse_json_list(value) -> list[dict]:
    if isinstance(value, list):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _genre_names(value) -> list[str]:
    return [item.get("name") for item in _parse_json_list(value) if isinstance(item, dict) and item.get("name")]


def _company(value) -> str | None:
    companies = _parse_json_list(value)
    if companies and isinstance(companies[0], dict):
        name = companies[0].get("name")
        return str(name) if name else None
    return None


def _director(value) -> str | None:
    crew = _parse_json_list(value)
    for member in crew:
        if isinstance(member, dict) and member.get("job") == "Director":
            name = member.get("name")
            return str(name) if name else None
    return None


def _cast_names(value) -> list[str]:
    cast = _parse_json_list(value)
    ordered = sorted(
        (item for item in cast if isinstance(item, dict)),
        key=lambda item: item.get("order", 10**6),
    )
    return [str(item.get("name")) for item in ordered[:TOP_CAST] if item.get("name")]


def load_raw(movies_path: str | Path, credits_path: str | Path) -> pd.DataFrame:
    movies_path = Path(movies_path)
    credits_path = Path(credits_path)

    if not movies_path.exists() or not credits_path.exists():
        raise FileNotFoundError(
            "Raw dataset files are missing. Place `tmdb_5000_movies.csv` and "
            "`tmdb_5000_credits.csv` in backend/data/raw/ (see README for download "
            "instructions), or run `python scripts/download_data.py`."
        )

    movies = pd.read_csv(movies_path, low_memory=False)
    credits = pd.read_csv(credits_path, low_memory=False)

    if "id" not in movies.columns or "budget" not in movies.columns:
        raise ValueError(
            "movies CSV is missing required columns (id, budget, revenue, ...). "
            "Expected the TMDB 5000 dataset."
        )

    merged = movies.merge(credits[["movie_id", "cast", "crew"]], left_on="id", right_on="movie_id", how="left")
    return merged


def clean_and_engineer(df: pd.DataFrame) -> pd.DataFrame:
    initial = len(df)

    # --- status filter -----------------------------------------------------
    if "status" in df.columns:
        df = df[df["status"].fillna("Released").eq("Released")]

    # --- parse structured JSON columns --------------------------------------
    df = df.copy()
    df["genres"] = df["genres"].apply(_genre_names)
    df["primary_genre"] = df["genres"].apply(lambda g: g[0] if g else None)
    df["production_company"] = df["production_companies"].apply(_company)
    df["director"] = df["crew"].apply(_director)
    df["cast_names"] = df["cast"].apply(_cast_names)
    df["cast_size"] = df["cast_names"].apply(len)

    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df["release_year"] = df["release_date"].dt.year
    df["release_month"] = df["release_date"].dt.month
    df["release_quarter"] = ((df["release_month"].fillna(1).astype(int) - 1) // 3) + 1
    df["release_weekday"] = df["release_date"].dt.dayofweek
    df["release_date"] = df["release_date"].dt.strftime("%Y-%m-%d")

    # --- invalid value removal ---------------------------------------------
    for col in ("budget", "revenue", "runtime", "popularity", "vote_average", "vote_count"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["budget", "revenue"])
    df = df[df["budget"] > 0]
    df = df[df["revenue"] > 0]
    df = df[(df["runtime"] >= RUNTIME_MIN) & (df["runtime"] <= RUNTIME_MAX)]
    df = df[(df["release_year"] >= YEAR_MIN) & (df["release_year"] <= YEAR_MAX)]

    # --- duplicates ---------------------------------------------------------
    df = df.drop_duplicates(subset=["id"], keep="first")
    df = df.dropna(subset=["title"])

    # --- select & order columns ---------------------------------------------
    df["original_language"] = df["original_language"].fillna("en")
    df["popularity"] = df["popularity"].fillna(0.0)
    df["vote_average"] = df["vote_average"].fillna(df["vote_average"].median())
    df["vote_count"] = df["vote_count"].fillna(0)
    df["is_demo"] = 0

    for col in RAW_COLUMNS:
        if col not in df.columns:
            df[col] = None

    out = df[RAW_COLUMNS].copy()
    out["id"] = out["id"].astype(np.int64)

    # Serialize lists as JSON so they survive CSV round-trips and parse cleanly.
    out["genres"] = out["genres"].apply(lambda g: json.dumps(g) if isinstance(g, list) else "[]")
    out["cast_names"] = out["cast_names"].apply(lambda c: json.dumps(c) if isinstance(c, list) else "[]")

    logger.info(
        "Cleaned %d raw rows -> %d rows (dropped %d).",
        initial,
        len(out),
        initial - len(out),
    )
    return out


def load_and_engineer(
    movies_path: str | Path,
    credits_path: str | Path,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    df = load_raw(movies_path, credits_path)
    processed = clean_and_engineer(df)
    if output_path is not None:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        processed.to_csv(out_path, index=False)
        logger.info("Saved processed dataset to %s (%d rows).", out_path, len(processed))
    return processed
