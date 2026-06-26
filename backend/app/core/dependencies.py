"""Reusable FastAPI dependencies: DB session, current user and RBAC guards.

These centralize authentication/authorization so every protected endpoint reuses the
same logic (DRY) and RBAC is enforced consistently on every route (FR-01, NFR: Security).
"""
from typing import Iterable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import ACCESS_TOKEN_TYPE, JWTError, decode_token
from app.database import get_db
from app.models.user import User
from app.repositories import user_repository

# auto_error=False so we can raise our own consistent error envelope instead of
# FastAPI's default 403 for a missing Authorization header.
_bearer_scheme = HTTPBearer(auto_error=False, description="JWT access token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve and return the authenticated user from a Bearer access token."""
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Authentication credentials were not provided.")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise AuthenticationError("Invalid or expired access token.")

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise AuthenticationError("A valid access token is required.")

    subject = payload.get("sub")
    if subject is None:
        raise AuthenticationError("Malformed access token.")

    user = await user_repository.get_user_by_id(db, int(subject))
    if user is None:
        raise AuthenticationError("User account no longer exists.")
    if not user.is_active:
        raise AuthenticationError("This account is disabled.")
    return user


def get_user_permissions(user: User) -> set[str]:
    """Effective permission codes for a user, derived from their role."""
    if not user.role:
        return set()
    return {p.permission_code for p in user.role.permissions if not p.is_deleted}


class require_permission:  # noqa: N801 — used as a dependency factory, reads like a decorator
    """Dependency factory enforcing that the current user holds a given permission.

    Usage::

        @router.post(..., dependencies=[Depends(require_permission("BYELAW_UPLOAD"))])

    or to also receive the user::

        user: User = Depends(require_permission("BYELAW_UPLOAD"))
    """

    def __init__(self, *required: str) -> None:
        self._required: tuple[str, ...] = required

    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        held = get_user_permissions(user)
        missing = [code for code in self._required if code not in held]
        if missing:
            raise AuthorizationError(
                f"Missing required permission(s): {', '.join(missing)}."
            )
        return user


class require_role:  # noqa: N801
    """Dependency factory enforcing that the current user has one of the given roles."""

    def __init__(self, *roles: str) -> None:
        self._roles: tuple[str, ...] = roles

    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        role_name = user.role.role_name if user.role else None
        if role_name not in self._roles:
            raise AuthorizationError("Your role is not permitted to perform this action.")
        return user


def has_any_permission(user: User, codes: Iterable[str]) -> bool:
    """Convenience predicate for in-handler checks."""
    held = get_user_permissions(user)
    return any(code in held for code in codes)
