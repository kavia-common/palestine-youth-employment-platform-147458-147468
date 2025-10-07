from fastapi import APIRouter
from sqlalchemy import text

from src.data.db import session_scope

router = APIRouter(prefix="/api/employers", tags=["users"])


@router.get("/{user_id}", summary="Get employer profile")
def get_employer(user_id: str):
    """Return employer profile by user id."""
    with session_scope() as db:
        row = db.execute(
            text("select user_id, org_name, website, location, verified, created_at, updated_at from public.employers where user_id = :u"),
            {"u": user_id},
        ).mappings().first()
        return dict(row) if row else {}
