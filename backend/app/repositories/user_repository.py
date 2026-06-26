"""Data-access functions for users, roles, permissions and refresh-token sessions."""
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import Role, User, UserSession


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Fetch an active (non-deleted) user by username, eager-loading role + permissions."""
    stmt = (
        select(User)
        .where(User.username == username, User.is_deleted.is_(False))
        .options(selectinload(User.role).selectinload(Role.permissions))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Fetch a user by id, eager-loading role + permissions for RBAC checks."""
    stmt = (
        select(User)
        .where(User.user_id == user_id, User.is_deleted.is_(False))
        .options(selectinload(User.role).selectinload(Role.permissions))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_username_including_deleted(db: AsyncSession, username: str) -> Optional[User]:
    """Lookup by username across all rows (incl. soft-deleted) for uniqueness checks."""
    stmt = select(User).where(func.lower(User.username) == username.lower())
    result = await db.execute(stmt)
    return result.scalars().first()


async def list_users(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    search: Optional[str] = None,
    role_id: Optional[int] = None,
    is_active: Optional[bool] = None,
) -> tuple[Sequence[User], int]:
    """Return a page of users plus the total count, honouring optional filters."""
    filters = [User.is_deleted.is_(False)]
    if search:
        like = f"%{search.strip()}%"
        filters.append(
            or_(
                User.username.ilike(like),
                User.full_name.ilike(like),
                User.email.ilike(like),
            )
        )
    if role_id is not None:
        filters.append(User.role_id == role_id)
    if is_active is not None:
        filters.append(User.is_active.is_(is_active))

    count_stmt = select(func.count()).select_from(User).where(*filters)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(User)
        .where(*filters)
        .options(selectinload(User.role))
        .order_by(User.user_id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return rows, total


async def create_user(db: AsyncSession, user: User) -> User:
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def count_active_admins(db: AsyncSession, admin_role_id: int, exclude_user_id: Optional[int] = None) -> int:
    """Count active, non-deleted users holding the Administrator role."""
    filters = [
        User.role_id == admin_role_id,
        User.is_active.is_(True),
        User.is_deleted.is_(False),
    ]
    if exclude_user_id is not None:
        filters.append(User.user_id != exclude_user_id)
    stmt = select(func.count()).select_from(User).where(*filters)
    return (await db.execute(stmt)).scalar_one()


# --- Refresh-token session management -------------------------------------------------

async def create_session(
    db: AsyncSession, user_id: int, refresh_token: str, expires_at: datetime
) -> UserSession:
    """Persist a refresh-token session so the token can later be validated/revoked."""
    session = UserSession(
        user_id=user_id,
        refresh_token=refresh_token,
        expires_at=expires_at,
        is_revoked=False,
    )
    db.add(session)
    await db.flush()
    return session


async def get_session_by_token(db: AsyncSession, refresh_token: str) -> Optional[UserSession]:
    stmt = select(UserSession).where(UserSession.refresh_token == refresh_token)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def revoke_session(db: AsyncSession, refresh_token: str) -> bool:
    """Revoke a single session by its refresh token. Returns True if a row was affected."""
    stmt = (
        update(UserSession)
        .where(UserSession.refresh_token == refresh_token, UserSession.is_revoked.is_(False))
        .values(is_revoked=True)
    )
    result = await db.execute(stmt)
    return (result.rowcount or 0) > 0


async def revoke_all_user_sessions(db: AsyncSession, user_id: int) -> int:
    """Revoke every active session for a user (e.g. on password change). Returns count."""
    stmt = (
        update(UserSession)
        .where(UserSession.user_id == user_id, UserSession.is_revoked.is_(False))
        .values(is_revoked=True)
    )
    result = await db.execute(stmt)
    return result.rowcount or 0
