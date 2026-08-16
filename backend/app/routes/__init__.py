from .analytics import router as analytics_router
from .health import router as health_router
from .model_info import router as model_info_router
from .movies import router as movies_router
from .predict import router as predict_router
from .training import router as training_router

__all__ = [
    "analytics_router",
    "health_router",
    "model_info_router",
    "movies_router",
    "predict_router",
    "training_router",
]
