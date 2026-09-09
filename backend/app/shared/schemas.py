"""Common Pydantic schemas shared across modules."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    status: int
    message: str
    correlation_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str
    db: str | None = None


class Page(BaseModel):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class PagedResponse(BaseModel, Generic[T]):
    items: list[T]
    limit: int
    offset: int
    total: int | None = None
