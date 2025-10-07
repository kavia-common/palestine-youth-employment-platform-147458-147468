from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import HTTPException, status
from jose import jwt, JWTError
from passlib.context import CryptContext

from src.core.config import get_settings

# Use pbkdf2_sha256 to avoid native bcrypt wheel/compilation issues in constrained environments.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a password using passlib (pbkdf2_sha256)."""
    return pwd_context.hash(password)


# PUBLIC_INTERFACE
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hash (pbkdf2_sha256)."""
    return pwd_context.verify(plain_password, hashed_password)


# PUBLIC_INTERFACE
def create_access_token(subject: str, extra_claims: Optional[Dict[str, Any]] = None, expires_minutes: Optional[int] = None) -> str:
    """Create a signed JWT access token for API auth."""
    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    exp_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=exp_minutes)).timestamp()),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


# PUBLIC_INTERFACE
def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate an API JWT token."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


# PUBLIC_INTERFACE
def create_supabase_realtime_jwt(subject: str, role: str = "authenticated", channels: Optional[list[str]] = None, expires_minutes: int = 60) -> str:
    """Mint a Supabase Realtime-compatible JWT using Supabase JWT secret.

    Notes:
    - 'role' should typically be 'authenticated' or 'service_role' for server->server use.
    - Include 'sub' as the user id (UUID string) for RLS policies.
    - Optionally include channel claims if you implement channel-based restrictions.
    """
    settings = get_settings()
    if not settings.SUPABASE_JWT_SECRET:
        raise HTTPException(status_code=500, detail="SUPABASE_JWT_SECRET is not configured")

    now = datetime.now(tz=timezone.utc)
    claims: Dict[str, Any] = {
        "role": role,
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    if channels:
        claims["allowed_channels"] = channels

    return jwt.encode(claims, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
