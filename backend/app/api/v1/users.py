"""User management endpoints (M3, FRS Section 2.3 — Administrator function).

Every endpoint is protected by a specific permission. The ``/users/me/change-password``
endpoint is available to any authenticated user for their own account.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_permission
from app.database import get_db
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import (
    AdminPasswordResetRequest,
    ChangePasswordRequest,
    UserCreateRequest,
    UserDetailResponse,
    UserUpdateRequest,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get(
    "",
    response_model=PaginatedResponse[UserDetailResponse],
    summary="List users (paginated, filterable)",
)
async def list_users(
    page: int = Query(1, ge=1, description="1-based page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    search: Optional[str] = Query(None, description="Match username, full name or email"),
    role_id: Optional[int] = Query(None, ge=1, description="Filter by role id"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    _: User = Depends(require_permission("USER_READ")),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[UserDetailResponse]:
    return await user_service.list_users(
        db, page=page, page_size=page_size, search=search, role_id=role_id, is_active=is_active
    )


@router.post(
    "",
    response_model=UserDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
async def create_user(
    payload: UserCreateRequest,
    actor: User = Depends(require_permission("USER_CREATE")),
    db: AsyncSession = Depends(get_db),
) -> UserDetailResponse:
    return await user_service.create_user(db, payload, actor)


@router.post(
    "/me/change-password",
    response_model=MessageResponse,
    summary="Change your own password",
)
async def change_own_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await user_service.change_own_password(db, current_user, payload)
    return MessageResponse(message="Password changed successfully. Please log in again.")


@router.get(
    "/{user_id}",
    response_model=UserDetailResponse,
    summary="Get a single user by id",
)
async def get_user(
    user_id: int = Path(..., ge=1),
    _: User = Depends(require_permission("USER_READ")),
    db: AsyncSession = Depends(get_db),
) -> UserDetailResponse:
    return await user_service.get_user(db, user_id)


@router.put(
    "/{user_id}",
    response_model=UserDetailResponse,
    summary="Update a user's details, role or active status",
)
async def update_user(
    payload: UserUpdateRequest,
    user_id: int = Path(..., ge=1),
    actor: User = Depends(require_permission("USER_UPDATE")),
    db: AsyncSession = Depends(get_db),
) -> UserDetailResponse:
    return await user_service.update_user(db, user_id, payload, actor)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Soft-delete a user",
)
async def delete_user(
    user_id: int = Path(..., ge=1),
    actor: User = Depends(require_permission("USER_DELETE")),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await user_service.delete_user(db, user_id, actor)
    return MessageResponse(message="User deleted successfully.")


@router.post(
    "/{user_id}/reset-password",
    response_model=MessageResponse,
    summary="Administratively reset a user's password",
)
async def reset_password(
    payload: AdminPasswordResetRequest,
    user_id: int = Path(..., ge=1),
    actor: User = Depends(require_permission("USER_UPDATE")),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await user_service.reset_password(db, user_id, payload, actor)
    return MessageResponse(message="Password reset successfully. The user must log in again.")
