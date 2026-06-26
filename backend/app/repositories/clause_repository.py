"""Data-access functions for bye-law clauses (Child records)."""
from typing import Optional, Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.byelaw import ByelawClause


async def list_by_master(db: AsyncSession, master_id: int) -> Sequence[ByelawClause]:
    """All clauses for a bye-law, ordered for faithful reconstruction (FR-06/FR-10)."""
    stmt = (
        select(ByelawClause)
        .where(ByelawClause.master_id == master_id, ByelawClause.is_deleted.is_(False))
        .order_by(ByelawClause.display_order.asc())
    )
    return (await db.execute(stmt)).scalars().all()


async def get_clause(db: AsyncSession, clause_id: int) -> Optional[ByelawClause]:
    stmt = select(ByelawClause).where(
        ByelawClause.clause_id == clause_id, ByelawClause.is_deleted.is_(False)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def delete_by_master(db: AsyncSession, master_id: int) -> int:
    """Hard-delete all clauses of a bye-law (used before re-extraction)."""
    result = await db.execute(delete(ByelawClause).where(ByelawClause.master_id == master_id))
    return result.rowcount or 0


async def delete_subtree(db: AsyncSession, master_id: int, root_clause_id: int) -> int:
    """Hard-delete a clause and all of its descendants.

    Resolved explicitly (rather than relying on the self-referential relationship,
    which would null children's parent instead of deleting them).
    """
    rows = await list_by_master(db, master_id)
    children_by_parent: dict[int, list[int]] = {}
    for c in rows:
        children_by_parent.setdefault(c.parent_clause_id, []).append(c.clause_id)

    to_delete: list[int] = []
    stack = [root_clause_id]
    while stack:
        cid = stack.pop()
        to_delete.append(cid)
        stack.extend(children_by_parent.get(cid, []))

    result = await db.execute(delete(ByelawClause).where(ByelawClause.clause_id.in_(to_delete)))
    return result.rowcount or 0


async def max_display_order(db: AsyncSession, master_id: int) -> int:
    stmt = select(func.coalesce(func.max(ByelawClause.display_order), 0)).where(
        ByelawClause.master_id == master_id
    )
    return (await db.execute(stmt)).scalar_one()


async def add_clause(db: AsyncSession, clause: ByelawClause) -> ByelawClause:
    db.add(clause)
    await db.flush()
    await db.refresh(clause)
    return clause


async def count_by_master(db: AsyncSession, master_id: int) -> int:
    stmt = (
        select(func.count())
        .select_from(ByelawClause)
        .where(ByelawClause.master_id == master_id, ByelawClause.is_deleted.is_(False))
    )
    return (await db.execute(stmt)).scalar_one()
