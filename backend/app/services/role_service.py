"""Role & permission management service (M2/M3).

The four roles defined by the FRS (Section 2.3) are treated as *system roles*: they
may have their description/permissions tuned but cannot be renamed or deleted, so the
RBAC model the application depends on stays intact.
"""
from typing import List, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.logging_config import get_logger
from app.models.user import Permission, Role
from app.repositories import role_repository
from app.schemas.user import (
    PermissionResponse,
    RoleCreateRequest,
    RoleUpdateRequest,
    RoleWithPermissionsResponse,
)

logger = get_logger(__name__)

# System roles seeded from the FRS — protected from rename/delete.
SYSTEM_ROLES = frozenset(
    {"Administrator", "Data Entry Operator", "Verifying Officer", "Viewer"}
)


def _to_response(role: Role, user_count: int) -> RoleWithPermissionsResponse:
    return RoleWithPermissionsResponse(
        role_id=role.role_id,
        role_name=role.role_name,
        description=role.description,
        created_at=role.created_at,
        user_count=user_count,
        permissions=[
            PermissionResponse(
                permission_id=p.permission_id,
                permission_code=p.permission_code,
                description=p.description,
            )
            for p in sorted(role.permissions, key=lambda x: x.permission_code)
            if not p.is_deleted
        ],
    )


async def _resolve_permissions(db: AsyncSession, permission_ids: Sequence[int]) -> List[Permission]:
    unique_ids = list({pid for pid in permission_ids})
    perms = await role_repository.get_permissions_by_ids(db, unique_ids)
    found_ids = {p.permission_id for p in perms}
    missing = [pid for pid in unique_ids if pid not in found_ids]
    if missing:
        raise BadRequestError(f"Unknown permission id(s): {sorted(missing)}.")
    return list(perms)


async def list_roles(db: AsyncSession) -> List[RoleWithPermissionsResponse]:
    roles = await role_repository.list_roles(db)
    out: List[RoleWithPermissionsResponse] = []
    for role in roles:
        count = await role_repository.count_users_with_role(db, role.role_id)
        out.append(_to_response(role, count))
    return out


async def get_role(db: AsyncSession, role_id: int) -> RoleWithPermissionsResponse:
    role = await role_repository.get_role_by_id(db, role_id)
    if role is None:
        raise NotFoundError(f"Role with id {role_id} was not found.")
    count = await role_repository.count_users_with_role(db, role_id)
    return _to_response(role, count)


async def create_role(db: AsyncSession, payload: RoleCreateRequest, actor) -> RoleWithPermissionsResponse:
    existing = await role_repository.get_role_by_name(db, payload.role_name)
    if existing is not None:
        raise ConflictError(f"A role named '{payload.role_name}' already exists.")

    role = Role(
        role_name=payload.role_name,
        description=payload.description,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    role.permissions = await _resolve_permissions(db, payload.permission_ids)
    role = await role_repository.create_role(db, role)
    await db.commit()
    fresh = await role_repository.get_role_by_id(db, role.role_id)
    logger.info("Role '%s' (id=%s) created by '%s'.", fresh.role_name, fresh.role_id, actor.username)
    return _to_response(fresh, 0)


async def update_role(
    db: AsyncSession, role_id: int, payload: RoleUpdateRequest, actor
) -> RoleWithPermissionsResponse:
    role = await role_repository.get_role_by_id(db, role_id)
    if role is None:
        raise NotFoundError(f"Role with id {role_id} was not found.")

    if payload.description is not None:
        role.description = payload.description
    if payload.permission_ids is not None:
        role.permissions = await _resolve_permissions(db, payload.permission_ids)
    role.updated_by = actor.user_id

    await db.commit()
    fresh = await role_repository.get_role_by_id(db, role_id)
    count = await role_repository.count_users_with_role(db, role_id)
    logger.info("Role id=%s updated by '%s'.", role_id, actor.username)
    return _to_response(fresh, count)


async def delete_role(db: AsyncSession, role_id: int, actor) -> None:
    role = await role_repository.get_role_by_id(db, role_id)
    if role is None:
        raise NotFoundError(f"Role with id {role_id} was not found.")
    if role.role_name in SYSTEM_ROLES:
        raise BadRequestError(f"The system role '{role.role_name}' cannot be deleted.")

    assigned = await role_repository.count_users_with_role(db, role_id)
    if assigned > 0:
        raise BadRequestError(
            f"Cannot delete role '{role.role_name}': {assigned} user(s) are still assigned to it."
        )

    role.is_deleted = True
    role.updated_by = actor.user_id
    await db.commit()
    logger.info("Role id=%s ('%s') soft-deleted by '%s'.", role_id, role.role_name, actor.username)


async def list_permissions(db: AsyncSession) -> List[PermissionResponse]:
    perms = await role_repository.list_permissions(db)
    return [
        PermissionResponse(
            permission_id=p.permission_id,
            permission_code=p.permission_code,
            description=p.description,
        )
        for p in perms
    ]
