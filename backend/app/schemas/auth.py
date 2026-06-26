"""Authentication request/response schemas (FR-01)."""
from pydantic import BaseModel, Field

from app.schemas.user import UserProfileResponse


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100, examples=["admin"])
    password: str = Field(..., min_length=1, max_length=128, examples=["AdminPassword123"])


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """OAuth2-style token bundle returned on login and refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access-token lifetime in seconds


class LoginResponse(TokenResponse):
    """Login result: tokens plus the authenticated user's profile."""

    user: UserProfileResponse
