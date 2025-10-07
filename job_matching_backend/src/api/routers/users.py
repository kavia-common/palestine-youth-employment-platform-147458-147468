from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.data.db import session_scope
from src.services.profile_service import get_me, upsert_job_seeker, upsert_employer

router = APIRouter(prefix="/api/users", tags=["users"])


class SeekerProfileIn(BaseModel):
    bio: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    visibility: Optional[bool] = Field(default=True)
    desired_role: Optional[str] = Field(default=None)


class EmployerProfileIn(BaseModel):
    org_name: str = Field(..., description="Organization name")
    website: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    verified: Optional[bool] = Field(default=False)


@router.get("/me", summary="Get current user profile", description="Returns combined user, seeker/employer profile")
def me(user_id: str):
    """Return a combined view for a user id provided via query (in prod, derive from JWT)."""
    with session_scope() as db:
        data = get_me(db, user_id=user_id)
        if not data:
            raise HTTPException(status_code=404, detail="User not found")
        return data


@router.put("/me/seeker", summary="Upsert seeker profile")
def me_seeker_update(user_id: str, payload: SeekerProfileIn):
    """Create/update the job seeker profile for current user."""
    with session_scope() as db:
        data = upsert_job_seeker(db, user_id=user_id, data=payload.model_dump())
        return data


@router.put("/me/employer", summary="Upsert employer profile")
def me_employer_update(user_id: str, payload: EmployerProfileIn):
    """Create/update the employer profile for current user."""
    with session_scope() as db:
        data = upsert_employer(db, user_id=user_id, data=payload.model_dump())
        return data
