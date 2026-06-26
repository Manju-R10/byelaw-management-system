"""Search & retrieval endpoints (FR-08)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_permission
from app.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.search import ByelawSearchHit, ClauseSearchHit
from app.services import search_service

router = APIRouter(prefix="/search", tags=["Search"])


@router.get(
    "/clauses",
    response_model=PaginatedResponse[ClauseSearchHit],
    summary="Full-text clause search with society/chapter filters (FR-08)",
)
async def search_clauses(
    q: Optional[str] = Query(None, description="Free-text clause keyword(s)"),
    registration_no: Optional[str] = Query(None, description="Restrict to a society"),
    society_name: Optional[str] = Query(None),
    byelaw_title: Optional[str] = Query(None),
    chapter_no: Optional[str] = Query(None, description="Restrict to a chapter number"),
    active_only: bool = Query(False, description="Only clauses of active bye-law versions"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(require_permission("BYELAW_SEARCH")),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ClauseSearchHit]:
    return await search_service.search_clauses(
        db, q=q, registration_no=registration_no, society_name=society_name,
        byelaw_title=byelaw_title, chapter_no=chapter_no, active_only=active_only,
        page=page, page_size=page_size,
    )


@router.get(
    "/byelaws",
    response_model=PaginatedResponse[ByelawSearchHit],
    summary="Search bye-laws by society/title/keyword with clause-match counts (FR-08)",
)
async def search_byelaws(
    q: Optional[str] = Query(None, description="Keyword matched in clauses and metadata"),
    registration_no: Optional[str] = Query(None),
    society_name: Optional[str] = Query(None),
    byelaw_title: Optional[str] = Query(None),
    active_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(require_permission("BYELAW_SEARCH")),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ByelawSearchHit]:
    return await search_service.search_byelaws(
        db, q=q, registration_no=registration_no, society_name=society_name,
        byelaw_title=byelaw_title, active_only=active_only, page=page, page_size=page_size,
    )
