"""Search result schemas (FR-08)."""
from typing import List, Optional

from pydantic import BaseModel


class ClauseSearchHit(BaseModel):
    """A single matching clause with its parent bye-law context and a snippet."""

    clause_id: int
    master_id: int
    parent_clause_id: Optional[int] = None
    clause_level: int
    chapter_no: Optional[str] = None
    clause_no: Optional[str] = None
    clause_title: Optional[str] = None
    snippet: str
    display_order: int
    score: float
    # Parent bye-law context
    society_name: str
    society_registration_no: str
    byelaw_title: str
    byelaw_version: str
    is_active: bool
    matched_terms: List[str] = []


class ByelawSearchHit(BaseModel):
    """A bye-law matching the search, with a count of matching clauses."""

    master_id: int
    society_name: str
    society_registration_no: str
    byelaw_title: str
    byelaw_version: str
    is_active: bool
    extraction_status: str
    workflow_status: str
    total_clauses: int
    match_count: int
