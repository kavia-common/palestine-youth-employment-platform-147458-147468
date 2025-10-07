from fastapi import APIRouter
from sqlalchemy import text

from src.data.db import session_scope

router = APIRouter(prefix="/api/jobseekers", tags=["users"])


@router.get("/{user_id}", summary="Get job seeker profile")
def get_job_seeker(user_id: str):
    """Return job seeker profile by user id."""
    with session_scope() as db:
        row = db.execute(
            text("select user_id, bio, location, visibility, desired_role, created_at, updated_at from public.job_seekers where user_id = :u"),
            {"u": user_id},
        ).mappings().first()
        return dict(row) if row else {}
