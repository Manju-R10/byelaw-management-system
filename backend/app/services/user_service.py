"""User management service (M3): CRUD, password administration and safety rules.

Enforces government-grade safeguards: usernames are unique, the last active
Administrator can never be removed/demoted/deactivated, and administrators cannot
lock themselves out (NFR: Reliability/Security).
"""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.logging_config import get_logger
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import role_repository, user_repository
from app.schemas.common import PaginatedResponse
from app.schemas.user import (
    AdminPasswordResetRequest,
    ChangePasswordRequest,
    UserCreateRequest,
    UserDetailResponse,
    UserUpdateRequest,
)

logger = get_logger(__name__)

ADMINISTRATOR_ROLE = "Administrator"


def _to_detail(user: User) -> UserDetailResponse:
    return UserDetailResponse(
        user_id=user.user_id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        role_id=user.role_id,
        created_at=user.created_at,
        updated_at=user.updated_at,
        role_name=user.role.role_name if user.role else None,
    )


async def _get_user_or_404(db: AsyncSession, user_id: int) -> User:
    user = await user_repository.get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundError(f"User with id {user_id} was not found.")
    return user


async def _admin_role_id(db: AsyncSession) -> Optional[int]:
    role = await role_repository.get_role_by_name(db, ADMINISTRATOR_ROLE)
    return role.role_id if role else None


async def list_users(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    search: Optional[str],
    role_id: Optional[int],
    is_active: Optional[bool],
) -> PaginatedResponse[UserDetailResponse]:
    rows, total = await user_repository.list_users(
        db, page=page, page_size=page_size, search=search, role_id=role_id, is_active=is_active
    )
    items = [_to_detail(u) for u in rows]
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


async def get_user(db: AsyncSession, user_id: int) -> UserDetailResponse:
    user = await _get_user_or_404(db, user_id)
    return _to_detail(user)


async def create_user(db: AsyncSession, payload: UserCreateRequest, actor: User) -> UserDetailResponse:
    existing = await user_repository.get_user_by_username_including_deleted(db, payload.username)
    if existing is not None:
        raise ConflictError(f"Username '{payload.username}' is already taken.")

    role = await role_repository.get_role_by_id(db, payload.role_id)
    if role is None:
        raise BadRequestError(f"Role with id {payload.role_id} does not exist.")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role_id=payload.role_id,
        email=payload.email,
        is_active=payload.is_active,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    user = await user_repository.create_user(db, user)
    await db.commit()
    # Reload with role relationship for the response.
    fresh = await _get_user_or_404(db, user.user_id)
    logger.info("User '%s' (id=%s) created by '%s'.", fresh.username, fresh.user_id, actor.username)
    return _to_detail(fresh)


async def update_user(
    db: AsyncSession, user_id: int, payload: UserUpdateRequest, actor: User
) -> UserDetailResponse:
    user = await _get_user_or_404(db, user_id)
    admin_role_id = await _admin_role_id(db)

    # Determine the prospective state after the update.
    new_role_id = payload.role_id if payload.role_id is not None else user.role_id
    new_is_active = payload.is_active if payload.is_active is not None else user.is_active

    # Guard: do not allow removing the last active Administrator (by demotion/deactivation).
    is_currently_admin = admin_role_id is not None and user.role_id == admin_role_id and user.is_active
    will_remain_admin = admin_role_id is not None and new_role_id == admin_role_id and new_is_active
    if is_currently_admin and not will_remain_admin:
        remaining = await user_repository.count_active_admins(db, admin_role_id, exclude_user_id=user.user_id)
        if remaining == 0:
            raise BadRequestError(
                "Cannot demote or deactivate the last active Administrator."
            )
        if user.user_id == actor.user_id:
            raise BadRequestError("Administrators cannot remove their own administrator access.")

    if payload.role_id is not None and payload.role_id != user.role_id:
        role = await role_repository.get_role_by_id(db, payload.role_id)
        if role is None:
            raise BadRequestError(f"Role with id {payload.role_id} does not exist.")
        user.role_id = payload.role_id
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        user.email = payload.email
    if payload.is_active is not None:
        user.is_active = payload.is_active
        if payload.is_active is False:
            # Deactivation: revoke active sessions so the account cannot continue.
            await user_repository.revoke_all_user_sessions(db, user.user_id)
    user.updated_by = actor.user_id

    await db.commit()
    fresh = await _get_user_or_404(db, user.user_id)
    logger.info("User id=%s updated by '%s'.", user_id, actor.username)
    return _to_detail(fresh)


async def delete_user(db: AsyncSession, user_id: int, actor: User) -> None:
    user = await _get_user_or_404(db, user_id)
    if user.user_id == actor.user_id:
        raise BadRequestError("You cannot delete your own account.")

    admin_role_id = await _admin_role_id(db)
    if admin_role_id is not None and user.role_id == admin_role_id and user.is_active:
        remaining = await user_repository.count_active_admins(db, admin_role_id, exclude_user_id=user.user_id)
        if remaining == 0:
            raise BadRequestError("Cannot delete the last active Administrator.")

    user.is_deleted = True
    user.is_active = False
    user.updated_by = actor.user_id
    await user_repository.revoke_all_user_sessions(db, user.user_id)
    await db.commit()
    logger.info("User id=%s soft-deleted by '%s'.", user_id, actor.username)


async def reset_password(
    db: AsyncSession, user_id: int, payload: AdminPasswordResetRequest, actor: User
) -> None:
    user = await _get_user_or_404(db, user_id)
    user.password_hash = hash_password(payload.new_password)
    user.updated_by = actor.user_id
    # Force re-authentication everywhere after an administrative reset.
    await user_repository.revoke_all_user_sessions(db, user.user_id)
    await db.commit()
    logger.info("Password for user id=%s reset by administrator '%s'.", user_id, actor.username)


async def change_own_password(db: AsyncSession, actor: User, payload: ChangePasswordRequest) -> None:
    if not verify_password(payload.current_password, actor.password_hash):
        raise BadRequestError("The current password is incorrect.")
    if verify_password(payload.new_password, actor.password_hash):
        raise BadRequestError("The new password must be different from the current password.")
    actor.password_hash = hash_password(payload.new_password)
    actor.updated_by = actor.user_id
    await user_repository.revoke_all_user_sessions(db, actor.user_id)
    await db.commit()
    logger.info("User '%s' changed their own password.", actor.username)
