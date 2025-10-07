from typing import Optional, Dict, Any
from uuid import uuid4

from sqlalchemy.orm import Session

from src.core.security import create_access_token
from src.data.repositories.users import get_user_by_email, create_user


# PUBLIC_INTERFACE
def register_user(db: Session, email: str, password: str, user_type: str, full_name: Optional[str] = None) -> Dict[str, Any]:
    """Register a user in application users table (note: Supabase auth.users is managed separately)."""
    # In real flow, you would call Supabase auth API to create user and receive id.
    # Here we generate a UUID stub and store hash (for API-only local auth fallback).
    user_id = str(uuid4())
    # Note: In Supabase production flow, password is handled by GoTrue. Local hash omitted.
    user = create_user(db, user_id=user_id, email=email, user_type=user_type, full_name=full_name)
    token = create_access_token(subject=user["id"], extra_claims={"email": email, "role": user_type})
    return {"user": user, "access_token": token, "token_type": "bearer"}


# PUBLIC_INTERFACE
def login_user(db: Session, email: str, password: str) -> Dict[str, Any]:
    """Login a user. This is a stub that checks user existence; password verify skipped (Supabase usually handles auth)."""
    user = get_user_by_email(db, email=email)
    if not user:
        raise ValueError("Invalid credentials")
    # Stub: Assume password ok (since Supabase handles auth). To support local, verify hash from stored table.
    token = create_access_token(subject=user["id"], extra_claims={"email": email, "role": user["user_type"]})
    return {"user": user, "access_token": token, "token_type": "bearer"}


# PUBLIC_INTERFACE
def verify_otp(_: Session, email: str, otp: str) -> bool:
    """Stub for OTP verification when using passwordless/email OTP flows via Supabase."""
    # TODO: Integrate with Supabase's verify OTP endpoints if using gotrue.
    return True
