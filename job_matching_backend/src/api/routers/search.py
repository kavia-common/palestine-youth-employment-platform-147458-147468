from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.data.db import session_scope
from src.services.search_service import keyword_search_jobs, semantic_search_jobs_for_seeker

router = APIRouter(prefix="/api/search", tags=["search"])


class KeywordSearchIn(BaseModel):
    q: str = Field(..., description="Keyword to search")
    limit: int = Field(default=20)
    offset: int = Field(default=0)


@router.post("/jobs", summary="Keyword job search")
def search_jobs(payload: KeywordSearchIn):
    """Keyword search across published jobs."""
    with session_scope() as db:
        return keyword_search_jobs(db, q=payload.q, limit=payload.limit, offset=payload.offset)


@router.get("/semantic/jobs/{user_id}", summary="Semantic job search for seeker")
def semantic_jobs(user_id: str, k: int = 20):
    """Semantic job search using vector similarity for a seeker profile."""
    with session_scope() as db:
        return semantic_search_jobs_for_seeker(db, user_id=user_id, k=k)
