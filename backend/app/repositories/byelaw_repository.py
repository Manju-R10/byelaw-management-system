"""Data-access functions for bye-law master records and upload history."""
from typing import Optional, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.byelaw import ByelawMaster, UploadHistory


async def get_master_by_id(db: AsyncSession, master_id: int) -> Optional[ByelawMaster]:
    stmt = select(ByelawMaster).where(
        ByelawMaster.master_id == master_id, ByelawMaster.is_deleted.is_(False)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def find_duplicate(
    db: AsyncSession, registration_no: str, version: str
) -> Optional[ByelawMaster]:
    """Find a non-deleted bye-law with the same society registration no. and version."""
    stmt = select(ByelawMaster).where(
        func.lower(ByelawMaster.society_registration_no) == registration_no.lower(),
        ByelawMaster.byelaw_version == version,
        ByelawMaster.is_deleted.is_(False),
    )
    return (await db.execute(stmt)).scalars().first()


async def count_versions(db: AsyncSession, registration_no: str) -> int:
    """Count existing (non-deleted) bye-law versions for a society."""
    stmt = (
        select(func.count())
        .select_from(ByelawMaster)
        .where(
            func.lower(ByelawMaster.society_registration_no) == registration_no.lower(),
            ByelawMaster.is_deleted.is_(False),
        )
    )
    return (await db.execute(stmt)).scalar_one()


async def list_masters(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    search: Optional[str] = None,
    registration_no: Optional[str] = None,
    extraction_status: Optional[str] = None,
    workflow_status: Optional[str] = None,
) -> tuple[Sequence[ByelawMaster], int]:
    filters = [ByelawMaster.is_deleted.is_(False)]
    if search:
        like = f"%{search.strip()}%"
        filters.append(
            or_(
                ByelawMaster.society_name.ilike(like),
                ByelawMaster.byelaw_title.ilike(like),
                ByelawMaster.society_registration_no.ilike(like),
            )
        )
    if registration_no:
        filters.append(func.lower(ByelawMaster.society_registration_no) == registration_no.lower())
    if extraction_status:
        filters.append(ByelawMaster.extraction_status == extraction_status)
    if workflow_status:
        filters.append(ByelawMaster.workflow_status == workflow_status)

    total = (await db.execute(select(func.count()).select_from(ByelawMaster).where(*filters))).scalar_one()

    stmt = (
        select(ByelawMaster)
        .where(*filters)
        .order_by(ByelawMaster.master_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return rows, total


async def create_master(db: AsyncSession, master: ByelawMaster) -> ByelawMaster:
    db.add(master)
    await db.flush()
    await db.refresh(master)
    return master


async def add_upload_history(db: AsyncSession, history: UploadHistory) -> UploadHistory:
    db.add(history)
    await db.flush()
    return history
