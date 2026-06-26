"""User, role and permission request/response schemas."""
import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not any(c.isalpha() for c in value):
        raise ValueError("Password must contain at least one letter.")
    if not any(c.isdigit() for c in value):
        raise ValueError("Password must contain at least one digit.")
    return value


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    permission_id: int
    permission_code: str
    description: Optional[str] = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role_id: int
    role_name: str
    description: Optional[str] = None


class UserResponse(BaseModel):
    """Public representation of a user account (never includes the password hash)."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    full_name: str
    email: Optional[EmailStr] = None
    is_active: bool
    role_id: int
    created_at: datetime


class UserDetailResponse(UserResponse):
    """User representation enriched with the role name (for list/detail views)."""

    role_name: Optional[str] = None
    updated_at: Optional[datetime] = None


class UserProfileResponse(UserResponse):
    """Authenticated user's own profile, including role name and effective permissions."""

    role_name: str
    permissions: List[str] = []


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100, examples=["data_operator_1"])
    password: str = Field(..., min_length=8, max_length=128, examples=["StrongPass123"])
    full_name: str = Field(..., min_length=1, max_length=150)
    role_id: int = Field(..., ge=1)
    email: Optional[EmailStr] = None
    is_active: bool = True

    @field_validator("username")
    @classmethod
    def _username_format(cls, v: str) -> str:
        v = v.strip()
        if not _USERNAME_RE.match(v):
            raise ValueError("Username may only contain letters, digits, '.', '_' and '-'.")
        return v

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class UserUpdateRequest(BaseModel):
    """All fields optional — only provided fields are updated. Username is immutable."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=150)
    role_id: Optional[int] = Field(None, ge=1)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class AdminPasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class RoleWithPermissionsResponse(RoleResponse):
    """Role plus its assigned permissions and a count of users holding it."""

    permissions: List[PermissionResponse] = []
    user_count: int = 0
    created_at: Optional[datetime] = None


class RoleCreateRequest(BaseModel):
    role_name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    permission_ids: List[int] = Field(default_factory=list)

    @field_validator("role_name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        return v.strip()


class RoleUpdateRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=255)
    permission_ids: Optional[List[int]] = None
