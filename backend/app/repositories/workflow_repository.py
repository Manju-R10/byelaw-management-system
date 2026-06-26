"""Data-access for the approval workflow: history, version activation and notifications."""
from typing import Optional, Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import Notification
from app.models.byelaw import ByelawMaster, WorkflowHistory
from app.models.user import Role, User


async def add_history(db: AsyncSession, history: WorkflowHistory) -> WorkflowHistory:
    db.add(history)
    await db.flush()
    return history


async def list_history(db: AsyncSession, master_id: int) -> Sequence[WorkflowHistory]:
    stmt = (
        select(WorkflowHistory)
        .where(WorkflowHistory.master_id == master_id)
        .order_by(WorkflowHistory.changed_at.asc(), WorkflowHistory.history_id.asc())
    )
    return (await db.execute(stmt)).scalars().all()


async def list_versions(db: AsyncSession, registration_no: str) -> Sequence[ByelawMaster]:
    stmt = (
        select(ByelawMaster)
        .where(
            func.lower(ByelawMaster.society_registration_no) == registration_no.lower(),
            ByelawMaster.is_deleted.is_(False),
        )
        .order_by(ByelawMaster.uploaded_date.asc(), ByelawMaster.master_id.asc())
    )
    return (await db.execute(stmt)).scalars().all()


async def deactivate_other_versions(db: AsyncSession, registration_no: str, keep_master_id: int) -> int:
    """Clear is_active on all other versions of a society (FR-09: one active version)."""
    stmt = (
        update(ByelawMaster)
        .where(
            func.lower(ByelawMaster.society_registration_no) == registration_no.lower(),
            ByelawMaster.master_id != keep_master_id,
            ByelawMaster.is_deleted.is_(False),
            ByelawMaster.is_active.is_(True),
        )
        .values(is_active=False)
    )
    result = await db.execute(stmt)
    return result.rowcount or 0


async def get_active_user_ids_by_roles(db: AsyncSession, role_names: Sequence[str]) -> Sequence[int]:
    stmt = (
        select(User.user_id)
        .join(Role, Role.role_id == User.role_id)
        .where(
            Role.role_name.in_(role_names),
            User.is_active.is_(True),
            User.is_deleted.is_(False),
        )
    )
    return (await db.execute(stmt)).scalars().all()


async def add_notification(db: AsyncSession, notification: Notification) -> Notification:
    db.add(notification)
    await db.flush()
    return notification


async def list_notifications(
    db: AsyncSession, user_id: int, *, unread_only: bool, page: int, page_size: int
) -> tuple[Sequence[Notification], int, int]:
    """Return (page rows, total, unread_count) for a user's notifications."""
    base = [Notification.user_id == user_id]
    filters = list(base)
    if unread_only:
        filters.append(Notification.is_read.is_(False))

    total = (await db.execute(select(func.count()).select_from(Notification).where(*filters))).scalar_one()
    unread = (
        await db.execute(
            select(func.count()).select_from(Notification).where(*base, Notification.is_read.is_(False))
        )
    ).scalar_one()

    stmt = (
        select(Notification)
        .where(*filters)
        .order_by(Notification.created_at.desc(), Notification.notification_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return rows, total, unread


async def get_notification(db: AsyncSession, notification_id: int) -> Optional[Notification]:
    stmt = select(Notification).where(Notification.notification_id == notification_id)
    return (await db.execute(stmt)).scalar_one_or_none()


async def mark_notification_read(db: AsyncSession, notification_id: int, user_id: int) -> bool:
    stmt = (
        update(Notification)
        .where(
            Notification.notification_id == notification_id,
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    return (result.rowcount or 0) > 0


async def mark_all_read(db: AsyncSession, user_id: int) -> int:
    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    return result.rowcount or 0
