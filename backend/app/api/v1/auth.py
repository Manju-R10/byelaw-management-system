"""Authentication endpoints (FR-01): login, refresh, logout, current-user profile."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserProfileResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse, summary="Authenticate and obtain tokens")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    """Validate credentials and return access + refresh tokens with the user profile."""
    return await auth_service.login(db, payload.username, payload.password)


@router.post("/refresh", response_model=TokenResponse, summary="Rotate tokens using a refresh token")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Exchange a valid refresh token for a new access + refresh token pair."""
    return await auth_service.refresh_tokens(db, payload.refresh_token)


@router.post("/logout", response_model=MessageResponse, summary="Revoke a refresh token")
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    """Revoke the supplied refresh-token session. Idempotent."""
    await auth_service.logout(db, payload.refresh_token)
    return MessageResponse(message="Logged out successfully.")


@router.get("/me", response_model=UserProfileResponse, summary="Current authenticated user")
async def read_current_user(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    """Return the authenticated user's profile, role and effective permissions."""
    return auth_service.build_user_profile(current_user)
