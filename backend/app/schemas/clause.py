"""Bye-law clause schemas: extraction result, tree view and review/correction (FR-05/FR-07)."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ClauseResponse(BaseModel):
    """Flat representation of a single clause."""

    model_config = ConfigDict(from_attributes=True)

    clause_id: int
    master_id: int
    parent_clause_id: Optional[int] = None
    clause_level: int
    chapter_no: Optional[str] = None
    clause_no: Optional[str] = None
    clause_title: Optional[str] = None
    clause_text: str
    display_order: int
    updated_at: Optional[datetime] = None


class ClauseTreeNode(BaseModel):
    """Recursive clause node for the review tree / accordion view (FR-07)."""

    clause_id: int
    parent_clause_id: Optional[int] = None
    clause_level: int
    chapter_no: Optional[str] = None
    clause_no: Optional[str] = None
    clause_title: Optional[str] = None
    clause_text: str
    display_order: int
    children: List["ClauseTreeNode"] = Field(default_factory=list)


class ExtractionResultResponse(BaseModel):
    master_id: int
    total_chapters: int
    total_clauses: int
    extraction_status: str
    warnings: List[str] = Field(default_factory=list)
    message: str


class ClauseUpdateRequest(BaseModel):
    """Edit a clause during review. Only provided fields change (FR-07)."""

    clause_title: Optional[str] = Field(None, max_length=255)
    clause_text: Optional[str] = Field(None, min_length=1)
    clause_level: Optional[int] = Field(None, ge=1, le=6)
    chapter_no: Optional[str] = Field(None, max_length=50)
    clause_no: Optional[str] = Field(None, max_length=50)


class ClauseCreateRequest(BaseModel):
    """Manually add a clause during review (FR-07)."""

    parent_clause_id: Optional[int] = Field(None, ge=1)
    clause_level: int = Field(..., ge=1, le=6)
    chapter_no: Optional[str] = Field(None, max_length=50)
    clause_no: Optional[str] = Field(None, max_length=50)
    clause_title: Optional[str] = Field(None, max_length=255)
    clause_text: str = Field(..., min_length=1)


class ReorderItem(BaseModel):
    clause_id: int = Field(..., ge=1)
    parent_clause_id: Optional[int] = Field(None, ge=1)
    display_order: int = Field(..., ge=1)
    clause_level: Optional[int] = Field(None, ge=1, le=6)


class ReorderRequest(BaseModel):
    """Re-order and/or re-parent clauses in one operation (FR-07)."""

    items: List[ReorderItem] = Field(..., min_length=1)


ClauseTreeNode.model_rebuild()
