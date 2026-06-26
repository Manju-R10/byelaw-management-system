"""Data-access functions for roles and permissions."""
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import Permission, Role, User


async def list_roles(db: AsyncSession) -> Sequence[Role]:
    """All non-deleted roles with their permissions eager-loaded."""
    stmt = (
        select(Role)
        .where(Role.is_deleted.is_(False))
        .options(selectinload(Role.permissions))
        .order_by(Role.role_id.asc())
    )
    return (await db.execute(stmt)).scalars().all()


async def get_role_by_id(db: AsyncSession, role_id: int) -> Optional[Role]:
    stmt = (
        select(Role)
        .where(Role.role_id == role_id, Role.is_deleted.is_(False))
        .options(selectinload(Role.permissions))
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_role_by_name(db: AsyncSession, role_name: str) -> Optional[Role]:
    stmt = (
        select(Role)
        .where(func.lower(Role.role_name) == role_name.lower(), Role.is_deleted.is_(False))
        .options(selectinload(Role.permissions))
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_role(db: AsyncSession, role: Role) -> Role:
    db.add(role)
    await db.flush()
    await db.refresh(role)
    return role


async def count_users_with_role(db: AsyncSession, role_id: int) -> int:
    """Count active (non-deleted) users assigned to a role."""
    stmt = (
        select(func.count())
        .select_from(User)
        .where(User.role_id == role_id, User.is_deleted.is_(False))
    )
    return (await db.execute(stmt)).scalar_one()


async def list_permissions(db: AsyncSession) -> Sequence[Permission]:
    stmt = (
        select(Permission)
        .where(Permission.is_deleted.is_(False))
        .order_by(Permission.permission_code.asc())
    )
    return (await db.execute(stmt)).scalars().all()


async def get_permissions_by_ids(db: AsyncSession, permission_ids: Sequence[int]) -> Sequence[Permission]:
    if not permission_ids:
        return []
    stmt = select(Permission).where(
        Permission.permission_id.in_(set(permission_ids)),
        Permission.is_deleted.is_(False),
    )
    return (await db.execute(stmt)).scalars().all()
