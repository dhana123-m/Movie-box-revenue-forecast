"""Prediction request/response schemas with validation rules."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..ml.genres import GENRE_NAMES

# Validation limits -----------------------------------------------------------
BUDGET_MIN = 1
BUDGET_MAX = 5_000_000_000
RUNTIME_MIN = 30
RUNTIME_MAX = 420
RATING_MIN = 0.0
RATING_MAX = 10.0
POPULARITY_MIN = 0.0
POPULARITY_MAX = 10_000.0
VOTE_COUNT_MIN = 0
VOTE_COUNT_MAX = 10_000_000
DAY_MIN = 1
DAY_MAX = 31


class PredictRequest(BaseModel):
    """Input required to produce a box-office revenue forecast.

    All fields describe a movie *before* or *around* release, so the same
    payload can be used to forecast a movie that does not exist in the dataset.
    """

    model_config = ConfigDict(extra="ignore")

    title: str = Field(..., min_length=1, max_length=200)
    budget: float = Field(..., gt=0, description="Production budget in USD")
    runtime: float = Field(..., gt=0, description="Movie runtime in minutes")
    genres: list[str] = Field(default_factory=list, max_length=10)
    release_month: int = Field(1, ge=1, le=12)
    release_day: int = Field(15, ge=DAY_MIN, le=DAY_MAX)
    release_year: Optional[int] = Field(None, ge=1960, le=2100)
    production_company: Optional[str] = Field(None, max_length=200)
    director: Optional[str] = Field(None, max_length=200)
    lead_actors: list[str] = Field(default_factory=list, max_length=12)
    rating: float = Field(5.0, ge=RATING_MIN, le=RATING_MAX, description="IMDb rating (0-10)")
    vote_count: int = Field(0, ge=VOTE_COUNT_MIN, le=VOTE_COUNT_MAX)
    popularity: float = Field(0.0, ge=POPULARITY_MIN, le=POPULARITY_MAX)
    language: str = Field("en", min_length=2, max_length=10)

    @field_validator("genres")
    @classmethod
    def _valid_genres(cls, v: list[str]) -> list[str]:
        normalized = [g.strip() for g in v if g and g.strip()]
        invalid = set(normalized) - set(GENRE_NAMES)
        if invalid:
            raise ValueError(f"Unknown genre(s): {', '.join(sorted(invalid))}. Valid: {', '.join(GENRE_NAMES)}")
        return normalized

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be blank.")
        return v

    @field_validator("lead_actors")
    @classmethod
    def _clean_actors(cls, v: list[str]) -> list[str]:
        return [a.strip() for a in v if a and a.strip()]

    @field_validator("production_company", "director")
    @classmethod
    def _clean_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @model_validator(mode="after")
    def _check_budget(self) -> "PredictRequest":
        if self.budget > BUDGET_MAX:
            raise ValueError(f"Budget cannot exceed ${BUDGET_MAX:,}.")
        if self.runtime < RUNTIME_MIN or self.runtime > RUNTIME_MAX:
            raise ValueError(f"Runtime must be between {RUNTIME_MIN} and {RUNTIME_MAX} minutes.")
        return self


class FeatureContribution(BaseModel):
    feature: str
    label: str
    impact: Literal["positive", "negative", "neutral"]
    magnitude: float = Field(..., ge=0.0)


class PredictResponse(BaseModel):
    predicted_revenue: float = Field(..., ge=0.0)
    predicted_revenue_usd: str
    predicted_revenue_million: str
    predicted_revenue_crore: str
    performance_category: str
    budget: float
    revenue_budget_ratio: float
    confidence_score: float = Field(..., ge=0.0, le=100.0)
    expected_range: dict
    model: str = "Deep Neural Network"
    model_version: str
    contributions: list[FeatureContribution]
    disclaimer: str


class BatchPredictItem(BaseModel):
    """A single movie record inside a batch payload (row-based batch API)."""

    model_config = ConfigDict(extra="ignore")
    title: str = Field(..., min_length=1, max_length=200)
    budget: float = Field(..., gt=0)
    runtime: float = Field(..., gt=0)
    genres: list[str] = Field(default_factory=list)
    release_month: int = Field(1, ge=1, le=12)
    release_day: int = Field(15, ge=1, le=31)
    release_year: Optional[int] = None
    production_company: Optional[str] = None
    director: Optional[str] = None
    lead_actors: list[str] = Field(default_factory=list)
    rating: float = Field(5.0, ge=0.0, le=10.0)
    vote_count: int = Field(0, ge=0)
    popularity: float = Field(0.0, ge=0.0)
    language: str = "en"

    @field_validator("genres")
    @classmethod
    def _valid_genres(cls, v: list[str]) -> list[str]:
        normalized = [g.strip() for g in v if g and g.strip()]
        invalid = set(normalized) - set(GENRE_NAMES)
        if invalid:
            raise ValueError(f"Unknown genre(s): {', '.join(sorted(invalid))}")
        return normalized


class BatchRowResult(BaseModel):
    row: int
    title: Optional[str] = None
    status: Literal["success", "error"]
    predicted_revenue: Optional[float] = None
    predicted_revenue_usd: Optional[str] = None
    performance_category: Optional[str] = None
    error: Optional[str] = None


class BatchPredictResponse(BaseModel):
    total_rows: int
    successful: int
    failed: int
    results: list[BatchRowResult]
    summary: Optional[PredictResponse] = None
