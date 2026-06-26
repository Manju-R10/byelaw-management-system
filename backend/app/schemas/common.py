"""Shared response schemas reused across modules."""
import math
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class MessageResponse(BaseModel):
    """A simple success acknowledgement."""

    success: bool = True
    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic envelope for paginated list endpoints."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[object] = None


class ErrorResponse(BaseModel):
    """Canonical error envelope (documents the shape produced by exception handlers)."""

    success: bool = False
    error: ErrorDetail
