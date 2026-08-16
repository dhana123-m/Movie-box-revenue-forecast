"""Movie explorer endpoints (search, filter, paginate, sort)."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Movie
from ..config import settings
from ..ml.genres import GENRE_NAMES
from ..ml.performance import classify_performance
from ..schemas.common import ok
from ..schemas.movie import MovieDetail, MovieListResponse
from ..utils.errors import NotFoundError

router = APIRouter(tags=["movies"])

SORTABLE_COLUMNS = {
    "revenue": Movie.revenue,
    "budget": Movie.budget,
    "rating": Movie.rating,
    "year": Movie.release_year,
    "title": Movie.title,
    "popularity": Movie.popularity,
    "roi": None,  # computed property; handled specially
}


@router.get("/api/movies")
def list_movies(
    q: Optional[str] = None,
    genre: Optional[str] = None,
    year: Optional[int] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    sort_by: str = Query("revenue", pattern="^(revenue|budget|rating|year|title|popularity|roi)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Movie)

    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Movie.title.ilike(like), Movie.director.ilike(like), Movie.production_company.ilike(like))
        )
    if genre:
        stmt = stmt.where(Movie.primary_genre == genre)
    if year:
        stmt = stmt.where(Movie.release_year == year)
    if min_year:
        stmt = stmt.where(Movie.release_year >= min_year)
    if max_year:
        stmt = stmt.where(Movie.release_year <= max_year)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    if sort_by == "roi":
        rows = list(db.execute(stmt).scalars().all())
        rows.sort(key=lambda m: (m.roi if m.roi is not None else -1e18), reverse=order == "desc")
        rows = rows[(page - 1) * per_page : page * per_page]
    else:
        column = SORTABLE_COLUMNS[sort_by]
        column = column.desc() if order == "desc" else column.asc()
        rows = (
            db.execute(stmt.order_by(column).offset((page - 1) * per_page).limit(per_page))
            .scalars()
            .all()
        )

    return ok(
        MovieListResponse(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=(total + per_page - 1) // per_page,
            items=[_to_summary(m) for m in rows],
        ).model_dump()
    )


@router.get("/api/movies/{movie_id}")
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if movie is None:
        raise NotFoundError(f"Movie with id {movie_id} was not found.")
    return ok(_to_detail(movie).model_dump())


@router.get("/api/movies/filters/summary")
def filters_summary(db: Session = Depends(get_db)):
    """Distinct genres, year range, languages, companies and directors for dropdowns."""
    genres = db.execute(
        select(Movie.primary_genre).distinct().where(Movie.primary_genre.isnot(None)).order_by(Movie.primary_genre)
    ).scalars().all()
    # Only expose the canonical genres the prediction model understands.
    canonical = {g: i for i, g in enumerate(GENRE_NAMES)}
    genres = sorted(
        [g for g in genres if g in canonical],
        key=lambda g: canonical[g],
    )
    min_year = db.execute(select(func.min(Movie.release_year))).scalar_one_or_none()
    max_year = db.execute(select(func.max(Movie.release_year))).scalar_one_or_none()
    languages = db.execute(
        select(Movie.original_language)
        .distinct()
        .where(Movie.original_language.isnot(None), Movie.original_language != "")
        .order_by(Movie.original_language)
    ).scalars().all()
    companies = db.execute(
        select(Movie.production_company)
        .distinct()
        .where(Movie.production_company.isnot(None), Movie.production_company != "", Movie.production_company != "Unknown")
        .order_by(Movie.production_company)
    ).scalars().all()
    directors = db.execute(
        select(Movie.director)
        .distinct()
        .where(Movie.director.isnot(None), Movie.director != "", Movie.director != "Unknown")
        .order_by(Movie.director)
    ).scalars().all()
    return ok(
        {
            "genres": list(genres),
            "year_min": min_year,
            "year_max": max_year,
            "languages": list(languages),
            "companies": list(companies),
            "directors": list(directors),
        }
    )


def _parse_genres(value) -> list:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (TypeError, json.JSONDecodeError):
        return []


def _to_summary(movie: Movie) -> dict:
    return {
        "id": movie.id,
        "title": movie.title,
        "year": movie.release_year,
        "genres": _parse_genres(movie.genres),
        "primary_genre": movie.primary_genre,
        "budget": movie.budget,
        "revenue": movie.revenue,
        "roi": movie.roi,
        "rating": movie.rating,
        "popularity": movie.popularity,
        "classification": classify_performance(movie.revenue, movie.budget, settings.PERFORMANCE_THRESHOLDS),
        "director": movie.director,
        "production_company": movie.production_company,
        "runtime": movie.runtime,
        "original_language": movie.original_language,
        "vote_count": movie.vote_count,
        "release_date": movie.release_date,
    }


def _to_detail(movie: Movie) -> MovieDetail:
    return MovieDetail(
        id=movie.id,
        title=movie.title,
        year=movie.release_year,
        genres=_parse_genres(movie.genres),
        primary_genre=movie.primary_genre,
        budget=movie.budget,
        revenue=movie.revenue,
        roi=movie.roi,
        rating=movie.rating,
        popularity=movie.popularity,
        classification=classify_performance(movie.revenue, movie.budget, settings.PERFORMANCE_THRESHOLDS),
        tmdb_id=movie.tmdb_id,
        original_language=movie.original_language,
        production_company=movie.production_company,
        director=movie.director,
        runtime=movie.runtime,
        vote_count=movie.vote_count,
        cast_size=movie.cast_size,
        release_date=movie.release_date,
        release_month=movie.release_month,
        release_quarter=movie.release_quarter,
        release_weekday=movie.release_weekday,
        is_demo=bool(movie.is_demo),
    )
