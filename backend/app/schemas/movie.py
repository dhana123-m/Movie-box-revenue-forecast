"""Movie schemas for the explorer API."""

from typing import Optional

from pydantic import BaseModel, Field


class MovieSummary(BaseModel):
    id: int
    title: str
    year: Optional[int] = None
    genres: Optional[list[str]] = None
    primary_genre: Optional[str] = None
    budget: float
    revenue: float
    roi: Optional[float] = None
    rating: Optional[float] = None
    popularity: Optional[float] = None
    classification: Optional[str] = None
    director: Optional[str] = None
    production_company: Optional[str] = None
    runtime: Optional[float] = None
    original_language: Optional[str] = None
    vote_count: Optional[int] = None
    release_date: Optional[str] = None


class MovieDetail(MovieSummary):
    tmdb_id: Optional[int] = None
    original_language: Optional[str] = None
    production_company: Optional[str] = None
    director: Optional[str] = None
    runtime: Optional[float] = None
    vote_count: Optional[int] = None
    cast_size: Optional[int] = None
    release_date: Optional[str] = None
    release_month: Optional[int] = None
    release_quarter: Optional[int] = None
    release_weekday: Optional[int] = None
    is_demo: bool = False


class MovieListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    items: list[MovieSummary]
