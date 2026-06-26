"""Clause service: extraction orchestration and review/correction (FR-05/FR-06/FR-07)."""
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.logging_config import get_logger
from app.models.byelaw import ByelawClause, ByelawMaster
from app.models.user import User
from app.repositories import byelaw_repository, clause_repository
from app.schemas.byelaw import ByelawMasterResponse
from app.schemas.clause import (
    ClauseCreateRequest,
    ClauseResponse,
    ClauseTreeNode,
    ClauseUpdateRequest,
    ExtractionResultResponse,
    ReorderRequest,
)
from app.services import extraction_service

logger = get_logger(__name__)

_EXTRACTABLE_STATES = {"Pending", "Validated", "Failed", "Completed", "Reviewed"}


async def _get_master_or_404(db: AsyncSession, master_id: int) -> ByelawMaster:
    master = await byelaw_repository.get_master_by_id(db, master_id)
    if master is None:
        raise NotFoundError(f"Bye-law with id {master_id} was not found.")
    return master


async def _get_clause_or_404(db: AsyncSession, clause_id: int) -> ByelawClause:
    clause = await clause_repository.get_clause(db, clause_id)
    if clause is None:
        raise NotFoundError(f"Clause with id {clause_id} was not found.")
    return clause


async def run_extraction(db: AsyncSession, master_id: int, actor: User) -> ExtractionResultResponse:
    master = await _get_master_or_404(db, master_id)

    # Extraction (and thus re-extraction) is only permitted while the bye-law is a Draft.
    if master.workflow_status != "Draft":
        raise ConflictError(
            f"Extraction is only allowed while the bye-law is in 'Draft'; "
            f"current workflow status is '{master.workflow_status}'."
        )

    total, chapters, warnings = await extraction_service.extract_and_persist(db, master, actor.user_id)
    message = f"Extracted {total} clause(s) across {chapters} chapter(s)."
    if warnings:
        message += f" {len(warnings)} numbering anomaly(ies) flagged for review."
    return ExtractionResultResponse(
        master_id=master.master_id,
        total_chapters=chapters,
        total_clauses=total,
        extraction_status=master.extraction_status,
        warnings=warnings,
        message=message,
    )


async def get_clause_tree(db: AsyncSession, master_id: int) -> List[ClauseTreeNode]:
    await _get_master_or_404(db, master_id)
    clauses = await clause_repository.list_by_master(db, master_id)

    nodes: Dict[int, ClauseTreeNode] = {
        c.clause_id: ClauseTreeNode(
            clause_id=c.clause_id,
            parent_clause_id=c.parent_clause_id,
            clause_level=c.clause_level,
            chapter_no=c.chapter_no,
            clause_no=c.clause_no,
            clause_title=c.clause_title,
            clause_text=c.clause_text,
            display_order=c.display_order,
        )
        for c in clauses
    }
    roots: List[ClauseTreeNode] = []
    for c in clauses:  # already ordered by display_order
        node = nodes[c.clause_id]
        parent = nodes.get(c.parent_clause_id) if c.parent_clause_id else None
        if parent is not None:
            parent.children.append(node)
        else:
            roots.append(node)
    return roots


async def _refresh_counts(db: AsyncSession, master: ByelawMaster, actor_id: int) -> None:
    master.total_clauses = await clause_repository.count_by_master(db, master.master_id)
    master.updated_by = actor_id


async def update_clause(
    db: AsyncSession, clause_id: int, payload: ClauseUpdateRequest, actor: User
) -> ClauseResponse:
    clause = await _get_clause_or_404(db, clause_id)
    if payload.clause_title is not None:
        clause.clause_title = payload.clause_title or None
    if payload.clause_text is not None:
        clause.clause_text = payload.clause_text
    if payload.clause_level is not None:
        clause.clause_level = payload.clause_level
    if payload.chapter_no is not None:
        clause.chapter_no = payload.chapter_no or None
    if payload.clause_no is not None:
        clause.clause_no = payload.clause_no or None
    clause.updated_by = actor.user_id
    await db.commit()
    await db.refresh(clause)
    logger.info("Clause id=%s edited by '%s'.", clause_id, actor.username)
    return ClauseResponse.model_validate(clause)


async def add_clause(
    db: AsyncSession, master_id: int, payload: ClauseCreateRequest, actor: User
) -> ClauseResponse:
    master = await _get_master_or_404(db, master_id)
    if payload.parent_clause_id is not None:
        parent = await _get_clause_or_404(db, payload.parent_clause_id)
        if parent.master_id != master_id:
            raise BadRequestError("Parent clause belongs to a different bye-law.")

    next_order = (await clause_repository.max_display_order(db, master_id)) + 1
    clause = ByelawClause(
        master_id=master_id,
        parent_clause_id=payload.parent_clause_id,
        clause_level=payload.clause_level,
        chapter_no=payload.chapter_no or None,
        clause_no=payload.clause_no or None,
        clause_title=payload.clause_title or None,
        clause_text=payload.clause_text,
        display_order=next_order,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    clause = await clause_repository.add_clause(db, clause)
    await _refresh_counts(db, master, actor.user_id)
    await db.commit()
    await db.refresh(clause)
    logger.info("Clause id=%s added to master_id=%s by '%s'.", clause.clause_id, master_id, actor.username)
    return ClauseResponse.model_validate(clause)


async def delete_clause(db: AsyncSession, clause_id: int, actor: User) -> None:
    clause = await _get_clause_or_404(db, clause_id)
    master = await _get_master_or_404(db, clause.master_id)
    removed = await clause_repository.delete_subtree(db, master.master_id, clause_id)
    await db.flush()
    await _refresh_counts(db, master, actor.user_id)
    await db.commit()
    logger.info("Clause id=%s and %s descendant(s) deleted by '%s'.", clause_id, removed - 1, actor.username)


def _validate_no_cycles(parent_map: Dict[int, Optional[int]]) -> None:
    for start in parent_map:
        seen = set()
        cur: Optional[int] = start
        while cur is not None:
            if cur in seen:
                raise BadRequestError(f"Re-parenting would create a cycle at clause {start}.")
            seen.add(cur)
            cur = parent_map.get(cur)


async def reorder_clauses(
    db: AsyncSession, master_id: int, payload: ReorderRequest, actor: User
) -> List[ClauseTreeNode]:
    master = await _get_master_or_404(db, master_id)
    clauses = await clause_repository.list_by_master(db, master_id)
    by_id = {c.clause_id: c for c in clauses}

    # Validate ownership and parent references first.
    for item in payload.items:
        if item.clause_id not in by_id:
            raise BadRequestError(f"Clause {item.clause_id} does not belong to this bye-law.")
        if item.parent_clause_id is not None:
            if item.parent_clause_id == item.clause_id:
                raise BadRequestError(f"Clause {item.clause_id} cannot be its own parent.")
            if item.parent_clause_id not in by_id:
                raise BadRequestError(f"Parent clause {item.parent_clause_id} does not belong to this bye-law.")

    # Build the prospective parent map (only changing referenced clauses).
    parent_map: Dict[int, Optional[int]] = {c.clause_id: c.parent_clause_id for c in clauses}
    for item in payload.items:
        parent_map[item.clause_id] = item.parent_clause_id
    _validate_no_cycles(parent_map)

    for item in payload.items:
        clause = by_id[item.clause_id]
        clause.parent_clause_id = item.parent_clause_id
        clause.display_order = item.display_order
        if item.clause_level is not None:
            clause.clause_level = item.clause_level
        clause.updated_by = actor.user_id

    master.updated_by = actor.user_id
    await db.commit()
    logger.info("Reordered %s clause(s) for master_id=%s by '%s'.", len(payload.items), master_id, actor.username)
    return await get_clause_tree(db, master_id)


async def mark_reviewed(db: AsyncSession, master_id: int, actor: User) -> ByelawMasterResponse:
    master = await _get_master_or_404(db, master_id)
    if await clause_repository.count_by_master(db, master_id) == 0:
        raise BadRequestError("Cannot mark as reviewed: the bye-law has no clauses.")
    master.extraction_status = "Reviewed"
    master.reviewed_by = actor.user_id
    master.reviewed_date = datetime.utcnow()
    master.updated_by = actor.user_id
    await db.commit()
    await db.refresh(master)
    logger.info("Bye-law master_id=%s marked Reviewed by '%s'.", master_id, actor.username)
    return ByelawMasterResponse.model_validate(master)
