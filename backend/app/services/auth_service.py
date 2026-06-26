"""Authentication service: credential verification, token issuing, refresh and logout (FR-01).

Refresh tokens are persisted in ``user_sessions`` and rotated on every refresh so a
stolen refresh token has a bounded, revocable lifetime (NFR: Security).
"""
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AuthenticationError
from app.core.logging_config import get_logger
from app.core.security import (
    REFRESH_TOKEN_TYPE,
    JWTError,
    access_token_expires_in_seconds,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_password,
)
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import LoginResponse, TokenResponse
from app.schemas.user import UserProfileResponse

logger = get_logger(__name__)


def _build_token_claims(user: User) -> dict:
    """Claims embedded in every token so the role is available without a DB hit."""
    return {"role": user.role.role_name if user.role else None, "username": user.username}


def build_user_profile(user: User) -> UserProfileResponse:
    """Map a User ORM object (with role+permissions loaded) to its profile DTO."""
    permissions = []
    role_name = ""
    if user.role:
        role_name = user.role.role_name
        permissions = sorted(
            p.permission_code for p in user.role.permissions if not p.is_deleted
        )
    return UserProfileResponse(
        user_id=user.user_id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        role_id=user.role_id,
        created_at=user.created_at,
        role_name=role_name,
        permissions=permissions,
    )


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    """Validate credentials. Raises AuthenticationError on any failure.

    A single generic message is returned for unknown username, wrong password and
    disabled account so the endpoint does not leak which condition occurred.
    """
    user = await user_repository.get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        logger.warning("Failed login attempt for username '%s'.", username)
        raise AuthenticationError("Invalid username or password.")
    if not user.is_active:
        logger.warning("Login attempt on disabled account '%s'.", username)
        raise AuthenticationError("This account is disabled. Please contact an administrator.")
    return user


async def _issue_tokens(db: AsyncSession, user: User) -> TokenResponse:
    """Create an access + refresh token pair and persist the refresh session."""
    claims = _build_token_claims(user)
    access_token, _ = create_access_token(user.user_id, claims)
    refresh_token, _ = create_refresh_token(user.user_id, claims)

    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    # Persist only the hash of the refresh token, never the token itself.
    await user_repository.create_session(db, user.user_id, hash_token(refresh_token), expires_at)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=access_token_expires_in_seconds(),
    )


async def login(db: AsyncSession, username: str, password: str) -> LoginResponse:
    """Authenticate and return tokens + user profile."""
    user = await authenticate_user(db, username, password)
    tokens = await _issue_tokens(db, user)
    await db.commit()
    logger.info("User '%s' (id=%s) logged in successfully.", user.username, user.user_id)
    return LoginResponse(**tokens.model_dump(), user=build_user_profile(user))


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenResponse:
    """Validate a refresh token, rotate it and return a fresh token pair."""
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise AuthenticationError("Invalid or expired refresh token.")

    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise AuthenticationError("Provided token is not a refresh token.")

    token_digest = hash_token(refresh_token)
    session = await user_repository.get_session_by_token(db, token_digest)
    if session is None or session.is_revoked or session.expires_at < datetime.utcnow():
        raise AuthenticationError("Refresh token is no longer valid. Please log in again.")

    user = await user_repository.get_user_by_id(db, int(payload["sub"]))
    if user is None or not user.is_active:
        raise AuthenticationError("Account is unavailable.")

    # Rotate: revoke the presented token, issue a new pair.
    await user_repository.revoke_session(db, token_digest)
    tokens = await _issue_tokens(db, user)
    await db.commit()
    logger.info("Refresh-token rotation for user id=%s.", user.user_id)
    return tokens


async def logout(db: AsyncSession, refresh_token: str) -> None:
    """Revoke the supplied refresh-token session (idempotent)."""
    revoked = await user_repository.revoke_session(db, hash_token(refresh_token))
    await db.commit()
    if revoked:
        logger.info("Refresh token revoked on logout.")
