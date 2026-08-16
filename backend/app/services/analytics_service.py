"""Analytics computed from the stored historical movie data (real queries)."""

from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Movie
from ..schemas.analytics import (
    AnalyticsBudgetVsRevenue,
    AnalyticsGenre,
    AnalyticsOverview,
    AnalyticsTopMovie,
    AnalyticsYearly,
)


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------- overview --
    def overview(self) -> AnalyticsOverview:
        row = self.db.execute(
            select(
                func.count(Movie.id),
                func.avg(Movie.budget),
                func.avg(Movie.revenue),
                func.max(Movie.revenue),
                func.max(Movie.budget),
                func.sum(Movie.revenue),
                func.min(Movie.release_year),
                func.max(Movie.release_year),
            )
        ).one()
        top = self.db.execute(
            select(Movie.title).order_by(Movie.revenue.desc()).limit(1)
        ).scalar_one_or_none()

        # Median revenue (SQLite has no median aggregate).
        all_revenues = sorted(
            self.db.execute(select(Movie.revenue)).scalars().all()
        )
        median = _median(all_revenues)

        avg_roi = self.db.execute(
            select(func.avg((Movie.revenue - Movie.budget) / Movie.budget))
            .where(Movie.budget > 0)
        ).scalar_one_or_none()

        return AnalyticsOverview(
            total_movies=int(row[0] or 0),
            avg_budget=round(float(row[1] or 0), 2),
            avg_revenue=round(float(row[2] or 0), 2),
            median_revenue=round(median or 0, 2),
            highest_revenue=round(float(row[3] or 0), 2),
            highest_revenue_movie=str(top or "—"),
            highest_budget=round(float(row[4] or 0), 2),
            total_revenue=round(float(row[5] or 0), 2),
            avg_roi=round(float(avg_roi or 0), 2),
            year_min=int(row[6] or 0),
            year_max=int(row[7] or 0),
        )

    # -------------------------------------------------------------- genres ---
    def genres(self) -> list[AnalyticsGenre]:
        rows = self.db.execute(
            select(
                Movie.primary_genre,
                func.count(Movie.id),
                func.sum(Movie.revenue),
                func.avg(Movie.revenue),
                func.avg(Movie.budget),
            )
            .where(Movie.primary_genre.isnot(None))
            .group_by(Movie.primary_genre)
            .order_by(func.sum(Movie.revenue).desc())
        ).all()
        result = []
        for genre, count, total_rev, avg_rev, avg_budget in rows:
            avg_roi = self.db.execute(
                select(func.avg((Movie.revenue - Movie.budget) / Movie.budget))
                .where(Movie.primary_genre == genre, Movie.budget > 0)
            ).scalar_one_or_none()
            result.append(
                AnalyticsGenre(
                    genre=str(genre),
                    movie_count=int(count),
                    total_revenue=round(float(total_rev or 0), 2),
                    avg_revenue=round(float(avg_rev or 0), 2),
                    avg_budget=round(float(avg_budget or 0), 2),
                    avg_roi=round(float(avg_roi or 0), 2),
                )
            )
        return result

    # -------------------------------------------------------------- yearly ---
    def yearly(self, min_year: Optional[int] = None) -> list[AnalyticsYearly]:
        stmt = (
            select(
                Movie.release_year,
                func.count(Movie.id),
                func.sum(Movie.revenue),
                func.avg(Movie.revenue),
                func.sum(Movie.budget),
            )
            .where(Movie.release_year.isnot(None))
            .group_by(Movie.release_year)
            .order_by(Movie.release_year)
        )
        if min_year:
            stmt = stmt.where(Movie.release_year >= min_year)
        rows = self.db.execute(stmt).all()
        result = []
        for year, count, total_rev, avg_rev, total_budget in rows:
            avg_roi = self.db.execute(
                select(func.avg((Movie.revenue - Movie.budget) / Movie.budget))
                .where(Movie.release_year == year, Movie.budget > 0)
            ).scalar_one_or_none()
            result.append(
                AnalyticsYearly(
                    year=int(year),
                    movie_count=int(count),
                    total_revenue=round(float(total_rev or 0), 2),
                    avg_revenue=round(float(avg_rev or 0), 2),
                    total_budget=round(float(total_budget or 0), 2),
                    avg_roi=round(float(avg_roi or 0), 2),
                )
            )
        return result

    # ------------------------------------------------------------ scatter -----
    def budget_vs_revenue(self, limit: int = 500) -> list[AnalyticsBudgetVsRevenue]:
        rows = self.db.execute(
            select(Movie.title, Movie.release_year, Movie.budget, Movie.revenue)
            .order_by(Movie.revenue.desc())
            .limit(limit)
        ).all()
        return [
            AnalyticsBudgetVsRevenue(
                title=str(title),
                year=int(year) if year is not None else None,
                budget=round(float(budget), 2),
                revenue=round(float(revenue), 2),
            )
            for title, year, budget, revenue in rows
        ]

    # ----------------------------------------------------------- top movies --
    def top_movies(self, limit: int = 10) -> list[AnalyticsTopMovie]:
        rows = self.db.execute(
            select(
                Movie.title,
                Movie.release_year,
                Movie.budget,
                Movie.revenue,
                Movie.rating,
                Movie.primary_genre,
            )
            .order_by(Movie.revenue.desc())
            .limit(limit)
        ).all()
        return [
            AnalyticsTopMovie(
                title=str(title),
                year=int(year) if year is not None else None,
                budget=round(float(budget), 2),
                revenue=round(float(revenue), 2),
                roi=round((float(revenue) - float(budget)) / float(budget) * 100, 2)
                if budget > 0
                else None,
                rating=float(rating) if rating is not None else None,
                primary_genre=str(genre) if genre else None,
            )
            for title, year, budget, revenue, rating, genre in rows
        ]

    # ----------------------------------------------------- monthly trends ----
    def release_month_performance(self) -> list[dict]:
        rows = self.db.execute(
            select(
                Movie.release_month,
                func.count(Movie.id),
                func.avg(Movie.revenue),
                func.avg(Movie.revenue - Movie.budget),
            )
            .where(Movie.release_month.isnot(None))
            .group_by(Movie.release_month)
            .order_by(Movie.release_month)
        ).all()
        return [
            {
                "month": int(month),
                "label": _MONTH_LABELS.get(int(month), str(month)),
                "movie_count": int(count),
                "avg_revenue": round(float(avg_rev or 0), 2),
                "total_revenue": round(float((avg_rev or 0) * int(count)), 2),
                "avg_profit": round(float(avg_profit or 0), 2),
            }
            for month, count, avg_rev, avg_profit in rows
        ]

    def genre_revenue_by_year(self) -> list[dict]:
        rows = self.db.execute(
            select(
                Movie.release_year,
                Movie.primary_genre,
                func.sum(Movie.revenue),
                func.count(Movie.id),
            )
            .where(Movie.primary_genre.isnot(None), Movie.release_year.isnot(None))
            .group_by(Movie.release_year, Movie.primary_genre)
            .order_by(Movie.release_year)
        ).all()
        return [
            {
                "year": int(year),
                "genre": str(genre),
                "revenue": round(float(revenue or 0), 2),
                "count": int(count),
            }
            for year, genre, revenue, count in rows
        ]


_MONTH_LABELS = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
}


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    values = sorted(values)
    n = len(values)
    mid = n // 2
    if n % 2 == 1:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2.0
