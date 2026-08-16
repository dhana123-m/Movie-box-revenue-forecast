"""Application configuration loaded from environment variables.

All paths are resolved relative to the backend/ directory so the application
works out-of-the-box without setting extra environment variables.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = BACKEND_DIR / "models"
EVALUATION_DIR = MODELS_DIR / "evaluation"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Movie Box Office Revenue Forecast API"
    APP_VERSION: str = "1.0.0"
    MODEL_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = f"sqlite:///{BACKEND_DIR / 'movie_box.db'}"

    # Model artifacts
    MODEL_PATH: str = str(MODELS_DIR / "revenue_model.keras")
    PREPROCESSOR_PATH: str = str(MODELS_DIR / "preprocessor.pkl")
    METADATA_PATH: str = str(MODELS_DIR / "model_metadata.json")
    METRICS_PATH: str = str(MODELS_DIR / "metrics.json")
    FEATURE_CONFIG_PATH: str = str(MODELS_DIR / "feature_config.json")
    EVALUATION_DIR: str = str(MODELS_DIR / "evaluation")
    TRAINING_HISTORY_PATH: str = str(MODELS_DIR / "evaluation" / "training_history.json")
    PROCESSED_DATA_PATH: str = str(PROCESSED_DATA_DIR / "tmdb_5000_processed.csv")
    RAW_MOVIES_PATH: str = str(RAW_DATA_DIR / "tmdb_5000_movies.csv")
    RAW_CREDITS_PATH: str = str(RAW_DATA_DIR / "tmdb_5000_credits.csv")
    DEMO_DATA_PATH: str = str(RAW_DATA_DIR / "demo_movies.csv")

    # Built frontend (optional). When the folder exists, FastAPI serves the
    # production bundle on the same port, enabling single-port deployment.
    FRONTEND_DIST_PATH: str = str(BACKEND_DIR.parent / "frontend" / "dist")

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Box-office performance thresholds (revenue / budget multipliers).
    # Each value is the MINIMUM ratio required to reach that category:
    #   ratio < 1.0            -> FLOP
    #   1.0 <= ratio < 2.0     -> AVERAGE
    #   2.0 <= ratio < 4.0     -> HIT
    #   4.0 <= ratio < 8.0     -> SUPER_HIT
    #   ratio >= 8.0           -> BLOCKBUSTER
    PERFORMANCE_THRESHOLDS: dict = {
        "FLOP": 0.0,
        "AVERAGE": 1.0,
        "HIT": 2.0,
        "SUPER_HIT": 4.0,
        "BLOCKBUSTER": 8.0,
    }

    # Currency display (INR per 1 USD). Used only for display convenience.
    INR_PER_USD: float = 83.0

    # Training / retraining guard
    ALLOW_RETRAIN: bool = True

    # Upload limits (bytes) for batch CSV predictions
    MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024

    # Deep learning hyper-parameters (used by the training pipeline)
    LEARNING_RATE: float = 1e-3
    EPOCHS: int = 300
    BATCH_SIZE: int = 128
    VALIDATION_SPLIT: float = 0.15
    TEST_SPLIT: float = 0.15
    RANDOM_SEED: int = 42

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def performance_threshold_labels(self) -> list[str]:
        return list(self.PERFORMANCE_THRESHOLDS.keys())


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
