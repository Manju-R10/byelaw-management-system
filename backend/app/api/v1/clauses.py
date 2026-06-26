"""Extraction trigger and clause review/correction endpoints (FR-04/05/06/07)."""
from typing import List

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_permission
from app.database import get_db
from app.models.user import User
from app.schemas.byelaw import ByelawMasterResponse
from app.schemas.clause import (
    ClauseCreateRequest,
    ClauseResponse,
    ClauseTreeNode,
    ClauseUpdateRequest,
    ExtractionResultResponse,
    ReorderRequest,
)
from app.schemas.common import MessageResponse
from app.services import clause_service

# Extraction + tree endpoints are nested under a bye-law.
byelaw_clauses_router = APIRouter(prefix="/byelaws", tags=["Extraction & Review"])
# Single-clause edit/delete operate on a clause id directly.
clauses_router = APIRouter(prefix="/clauses", tags=["Extraction & Review"])


@byelaw_clauses_router.post(
    "/{master_id}/extract",
    response_model=ExtractionResultResponse,
    summary="Parse the uploaded document into a clause hierarchy and persist it (FR-04/05/06)",
)
async def extract_byelaw(
    master_id: int = Path(..., ge=1),
    actor: User = Depends(require_permission("BYELAW_EXTRACT")),
    db: AsyncSession = Depends(get_db),
) -> ExtractionResultResponse:
    return await clause_service.run_extraction(db, master_id, actor)


@byelaw_clauses_router.get(
    "/{master_id}/clauses",
    response_model=List[ClauseTreeNode],
    summary="Get the clause hierarchy (tree) for review/reading (FR-07/FR-08)",
)
async def get_clause_tree(
    master_id: int = Path(..., ge=1),
    _: User = Depends(require_permission("BYELAW_SEARCH")),
    db: AsyncSession = Depends(get_db),
) -> List[ClauseTreeNode]:
    return await clause_service.get_clause_tree(db, master_id)


@byelaw_clauses_router.post(
    "/{master_id}/clauses",
    response_model=ClauseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Manually add a clause during review (FR-07)",
)
async def add_clause(
    payload: ClauseCreateRequest,
    master_id: int = Path(..., ge=1),
    actor: User = Depends(require_permission("BYELAW_EDIT")),
    db: AsyncSession = Depends(get_db),
) -> ClauseResponse:
    return await clause_service.add_clause(db, master_id, payload, actor)


@byelaw_clauses_router.post(
    "/{master_id}/clauses/reorder",
    response_model=List[ClauseTreeNode],
    summary="Re-order and/or re-parent clauses (FR-07)",
)
async def reorder_clauses(
    payload: ReorderRequest,
    master_id: int = Path(..., ge=1),
    actor: User = Depends(require_permission("BYELAW_EDIT")),
    db: AsyncSession = Depends(get_db),
) -> List[ClauseTreeNode]:
    return await clause_service.reorder_clauses(db, master_id, payload, actor)


@byelaw_clauses_router.post(
    "/{master_id}/mark-reviewed",
    response_model=ByelawMasterResponse,
    summary="Mark the extracted bye-law as reviewed (FR-07)",
)
async def mark_reviewed(
    master_id: int = Path(..., ge=1),
    actor: User = Depends(require_permission("BYELAW_EDIT")),
    db: AsyncSession = Depends(get_db),
) -> ByelawMasterResponse:
    return await clause_service.mark_reviewed(db, master_id, actor)


@clauses_router.put(
    "/{clause_id}",
    response_model=ClauseResponse,
    summary="Edit a clause's text, title, level or numbering (FR-07)",
)
async def update_clause(
    payload: ClauseUpdateRequest,
    clause_id: int = Path(..., ge=1),
    actor: User = Depends(require_permission("BYELAW_EDIT")),
    db: AsyncSession = Depends(get_db),
) -> ClauseResponse:
    return await clause_service.update_clause(db, clause_id, payload, actor)


@clauses_router.delete(
    "/{clause_id}",
    response_model=MessageResponse,
    summary="Delete a clause and its sub-tree (FR-07)",
)
async def delete_clause(
    clause_id: int = Path(..., ge=1),
    actor: User = Depends(require_permission("BYELAW_EDIT")),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await clause_service.delete_clause(db, clause_id, actor)
    return MessageResponse(message="Clause deleted successfully.")
