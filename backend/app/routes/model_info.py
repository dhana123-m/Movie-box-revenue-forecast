"""Model information endpoint."""

from fastapi import APIRouter

from ..schemas.common import ok
from ..services.model_service import get_model_service

router = APIRouter(tags=["model"])


@router.get("/api/model/info")
def model_info():
    service = get_model_service()
    return ok(service.model_info())
