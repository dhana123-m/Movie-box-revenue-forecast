"""Shared API response envelope schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    fields: dict[str, str] | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


def ok(data: Any, message: str | None = None) -> dict:
    return {"success": True, "data": data, "message": message}


def error(code: str, message: str, fields: dict[str, str] | None = None) -> ErrorResponse:
    return ErrorResponse(error=ErrorDetail(code=code, message=message, fields=fields))
