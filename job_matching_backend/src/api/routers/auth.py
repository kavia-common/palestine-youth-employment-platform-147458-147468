from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr

from src.data.db import session_scope
from src.services.auth_service import register_user, login_user, verify_otp
from src.utils.supabase_jwt import mint_realtime_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="Password")
    user_type: str = Field(..., description="User type: job_seeker|employer|admin")
    full_name: Optional[str] = Field(default=None, description="Full name")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type, e.g., bearer")
    user: dict = Field(..., description="User object")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="Password")


class OTPVerifyRequest(BaseModel):
    email: EmailStr = Field(..., description="Email to verify")
    otp: str = Field(..., description="One-time passcode from email")


class RealtimeTokenResponse(BaseModel):
    token: str = Field(..., description="Supabase realtime JWT")
    expires_in_minutes: int = Field(..., description="Minutes until expiry")


@router.post("/register", response_model=TokenResponse, summary="Register user", description="Registers a user and returns API access token")
def register(payload: RegisterRequest):
    """Register a user in app table (Supabase auth is assumed external in production)."""
    with session_scope() as db:
        try:
            result = register_user(db, email=payload.email, password=payload.password, user_type=payload.user_type, full_name=payload.full_name)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        return result  # type: ignore


@router.post("/login", response_model=TokenResponse, summary="Login user", description="Logs in a user and returns API access token")
def login(payload: LoginRequest):
    """Login user (stub)."""
    with session_scope() as db:
        try:
            result = login_user(db, email=payload.email, password=payload.password)
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return result  # type: ignore


@router.post("/verify-otp", response_model=dict, summary="Verify OTP", description="Verify email OTP for passwordless flows")
def verify_otp_route(payload: OTPVerifyRequest):
    """Stub OTP verify using Supabase gotrue endpoints later."""
    with session_scope() as db:
        ok = verify_otp(db, email=payload.email, otp=payload.otp)
        return {"ok": ok}


@router.get("/realtime-token/{user_id}", response_model=RealtimeTokenResponse, summary="Mint realtime token", description="Mint a realtime JWT to use with Supabase Realtime subscriptions")
def realtime_token(user_id: str, minutes: int = 60):
    """Mint realtime JWT for given user id."""
    token = mint_realtime_token(user_id=user_id, minutes=minutes)
    return RealtimeTokenResponse(token=token, expires_in_minutes=minutes)
