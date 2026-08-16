"""Database seeding helpers.

The processed dataset (backend/data/processed/tmdb_5000_processed.csv) is
loaded into the ``movies`` table so the dashboard/analytics pages reflect the
exact data the model was trained on.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Movie

EXPECTED_SEED_COLUMNS = {
    "title",
    "budget",
    "revenue",
    "runtime",
    "release_date",
    "popularity",
    "vote_average",
    "vote_count",
    "original_language",
    "production_company",
    "director",
    "cast_names",
    "genres",
    "primary_genre",
    "is_demo",
}


def _parse_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value) if isinstance(value, str) else []
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def seed_from_csv(db: Session, csv_path: str | Path | None = None) -> int:
    """Insert processed movies into the DB. Returns the number inserted."""
    path = Path(csv_path or settings.PROCESSED_DATA_PATH)
    if not path.exists():
        return 0

    df = pd.read_csv(path)
    missing = EXPECTED_SEED_COLUMNS - set(df.columns)
    if missing:
        return 0

    inserted = 0
    for _, row in df.iterrows():
        genres = _parse_list(row.get("genres"))
        existing = db.execute(select(Movie.id).where(Movie.title == row["title"])).scalar_one_or_none()
        if existing is not None:
            continue
        movie = Movie(
            tmdb_id=int(row["id"]) if pd.notna(row.get("id")) else None,
            title=str(row["title"]),
            genres=json.dumps(genres),
            primary_genre=_first_genre(genres),
            original_language=_clean(row.get("original_language")),
            production_company=_clean(row.get("production_company")),
            director=_clean(row.get("director")),
            budget=float(row["budget"]),
            revenue=float(row["revenue"]),
            runtime=_nan_float(row.get("runtime")),
            rating=_nan_float(row.get("vote_average")),
            vote_count=_nan_int(row.get("vote_count")),
            popularity=_nan_float(row.get("popularity")),
            cast_size=_nan_int(row.get("cast_size")),
            release_date=_clean(row.get("release_date")),
            release_year=_nan_int(row.get("release_year")),
            release_month=_nan_int(row.get("release_month")),
            release_quarter=_nan_int(row.get("release_quarter")),
            release_weekday=_nan_int(row.get("release_weekday")),
            is_demo=int(row.get("is_demo") or 0),
        )
        db.add(movie)
        inserted += 1
        if inserted % 500 == 0:
            db.flush()
    db.commit()
    return inserted


def seed_database(db: Session) -> dict:
    """Seed the DB if it is empty. Returns a small status dict."""
    count = db.execute(select(Movie.id)).scalars().all()
    if count:
        return {"seeded": False, "movies": len(count)}
    inserted = seed_from_csv(db)
    return {"seeded": inserted > 0, "movies": inserted}


def _clean(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    return s or None


def _nan_float(value) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return float(value)


def _nan_int(value) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return int(value)


def _first_genre(genres: list[str]) -> str | None:
    return genres[0] if genres else None
