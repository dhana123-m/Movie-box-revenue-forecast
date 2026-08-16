"""Error hierarchy + FastAPI exception handlers.

The frontend receives a stable error envelope and never a raw Python traceback.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Base application error carrying an HTTP status and error code."""

    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message: str, fields: dict[str, str] | None = None) -> None:
        self.message = message
        self.fields = fields
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class InvalidInputError(AppError):
    status_code = 400
    code = "INVALID_INPUT"


class ModelNotAvailableError(AppError):
    status_code = 503
    code = "MODEL_UNAVAILABLE"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"


def _error_body(code: str, message: str, fields: dict[str, str] | None = None) -> dict:
    return {"success": False, "error": {"code": code, "message": message, "fields": fields}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, exc.fields),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields: dict[str, str] = {}
        for err in exc.errors():
            loc = ".".join(str(part) for part in err.get("loc", []) if part not in ("body", "query", "path"))
            fields[loc or "input"] = err.get("msg", "Invalid value")
        return JSONResponse(
            status_code=422,
            content=_error_body("VALIDATION_ERROR", "One or more fields failed validation.", fields),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body("HTTP_ERROR", str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_ERROR", "An unexpected error occurred. Please try again."),
        )
