from fastapi import APIRouter

from src.data.db import session_scope
from src.services.matching_service import basic_match_for_seeker

router = APIRouter(prefix="/api/match", tags=["match"])


@router.get("/seeker/{user_id}", summary="Basic matching for seeker")
def match_for_seeker(user_id: str, limit: int = 10):
    """Basic matching stub based on location and desired role."""
    with session_scope() as db:
        return basic_match_for_seeker(db, user_id=user_id, limit=limit)
