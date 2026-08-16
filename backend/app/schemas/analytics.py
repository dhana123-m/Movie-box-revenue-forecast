"""Analytics response schemas."""

from typing import Optional

from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total_movies: int
    avg_budget: float
    avg_revenue: float
    median_revenue: float
    highest_revenue: float
    highest_revenue_movie: str
    highest_budget: float
    total_revenue: float
    avg_roi: float
    year_min: int
    year_max: int


class AnalyticsGenre(BaseModel):
    genre: str
    movie_count: int
    total_revenue: float
    avg_revenue: float
    avg_budget: float
    avg_roi: float


class AnalyticsYearly(BaseModel):
    year: int
    movie_count: int
    total_revenue: float
    avg_revenue: float
    total_budget: float
    avg_roi: float


class AnalyticsBudgetVsRevenue(BaseModel):
    budget: float
    revenue: float
    title: str
    year: Optional[int] = None


class AnalyticsTopMovie(BaseModel):
    title: str
    year: Optional[int] = None
    budget: float
    revenue: float
    roi: Optional[float] = None
    rating: Optional[float] = None
    primary_genre: Optional[str] = None
