"""Role & permission management endpoints (M2/M3 — Administrator function)."""
from typing import List

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_permission
from app.database import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.user import (
    PermissionResponse,
    RoleCreateRequest,
    RoleUpdateRequest,
    RoleWithPermissionsResponse,
)
from app.services import role_service

router = APIRouter(prefix="/roles", tags=["Role Management"])
permissions_router = APIRouter(prefix="/permissions", tags=["Role Management"])


@router.get(
    "",
    response_model=List[RoleWithPermissionsResponse],
    summary="List all roles with their permissions and user counts",
)
async def list_roles(
    _: User = Depends(require_permission("ROLE_READ")),
    db: AsyncSession = Depends(get_db),
) -> List[RoleWithPermissionsResponse]:
    return await role_service.list_roles(db)


@router.post(
    "",
    response_model=RoleWithPermissionsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
)
async def create_role(
    payload: RoleCreateRequest,
    actor: User = Depends(require_permission("ROLE_CREATE")),
    db: AsyncSession = Depends(get_db),
) -> RoleWithPermissionsResponse:
    return await role_service.create_role(db, payload, actor)


@router.get(
    "/{role_id}",
    response_model=RoleWithPermissionsResponse,
    summary="Get a single role by id",
)
async def get_role(
    role_id: int = Path(..., ge=1),
    _: User = Depends(require_permission("ROLE_READ")),
    db: AsyncSession = Depends(get_db),
) -> RoleWithPermissionsResponse:
    return await role_service.get_role(db, role_id)


@router.put(
    "/{role_id}",
    response_model=RoleWithPermissionsResponse,
    summary="Update a role's description and/or assigned permissions",
)
async def update_role(
    payload: RoleUpdateRequest,
    role_id: int = Path(..., ge=1),
    actor: User = Depends(require_permission("ROLE_UPDATE")),
    db: AsyncSession = Depends(get_db),
) -> RoleWithPermissionsResponse:
    return await role_service.update_role(db, role_id, payload, actor)


@router.delete(
    "/{role_id}",
    response_model=MessageResponse,
    summary="Delete a non-system role (must have no assigned users)",
)
async def delete_role(
    role_id: int = Path(..., ge=1),
    actor: User = Depends(require_permission("ROLE_DELETE")),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await role_service.delete_role(db, role_id, actor)
    return MessageResponse(message="Role deleted successfully.")


@permissions_router.get(
    "",
    response_model=List[PermissionResponse],
    summary="List the catalogue of assignable permissions",
)
async def list_permissions(
    _: User = Depends(require_permission("PERMISSION_READ")),
    db: AsyncSession = Depends(get_db),
) -> List[PermissionResponse]:
    return await role_service.list_permissions(db)
