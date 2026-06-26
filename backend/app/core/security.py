"""Security primitives: password hashing and JWT token issuing/verification.

Passwords are stored as bcrypt salted hashes (FR-01, NFR: Security). Access and
refresh tokens are signed JWTs (HS256) carrying the user id, role and a unique
``jti`` so individual tokens can be tracked and refresh tokens revoked.
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings

# bcrypt only consumes the first 72 bytes of a password; longer inputs raise in
# bcrypt>=4. We truncate defensively so hashing/verification never crash.
_BCRYPT_MAX_BYTES = 72

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def _truncate_password(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    """Return a bcrypt salted hash for the given plaintext password."""
    hashed = bcrypt.hashpw(_truncate_password(password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(_truncate_password(plain_password), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed/empty hash — treat as a failed verification rather than crashing.
        return False


def _create_token(
    subject: Any,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: Optional[dict[str, Any]] = None,
) -> tuple[str, dict[str, Any]]:
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": uuid.uuid4().hex,
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, payload


def create_access_token(
    subject: Any, extra_claims: Optional[dict[str, Any]] = None
) -> tuple[str, dict[str, Any]]:
    """Create a short-lived access token. Returns (token, claims)."""
    return _create_token(
        subject,
        ACCESS_TOKEN_TYPE,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims,
    )


def create_refresh_token(
    subject: Any, extra_claims: Optional[dict[str, Any]] = None
) -> tuple[str, dict[str, Any]]:
    """Create a long-lived refresh token. Returns (token, claims)."""
    return _create_token(
        subject,
        REFRESH_TOKEN_TYPE,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        extra_claims,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT. Raises jose.JWTError on any failure (expiry, signature)."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def access_token_expires_in_seconds() -> int:
    """Lifetime of an access token in seconds (for the OAuth2 ``expires_in`` field)."""
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def hash_token(token: str) -> str:
    """Return a SHA-256 hex digest (64 chars) of a token.

    Refresh tokens are stored as this digest rather than in plaintext, so a database
    leak does not expose usable refresh tokens (NFR: Security). The digest also fits
    the ``user_sessions.refresh_token`` VARCHAR(255) column.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


__all__ = [
    "ACCESS_TOKEN_TYPE",
    "REFRESH_TOKEN_TYPE",
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "access_token_expires_in_seconds",
    "hash_token",
    "JWTError",
]
