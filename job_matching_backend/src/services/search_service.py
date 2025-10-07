from typing import Dict, List, Any
from sqlalchemy import text
from sqlalchemy.orm import Session


# PUBLIC_INTERFACE
def keyword_search_jobs(db: Session, q: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """Simple keyword search across title and description."""
    rows = db.execute(
        text(
            """
            select j.id, j.title, j.description, j.location, j.employment_type, j.salary_min, j.salary_max,
                   j.currency, j.is_remote, j.is_published, j.posted_at, j.expires_at
            from public.jobs j
            where j.is_published = true and (j.title ilike :q or j.description ilike :q)
            order by j.posted_at desc
            limit :limit offset :offset
            """
        ),
        {"q": f"%{q}%", "limit": limit, "offset": offset},
    ).mappings().all()
    return [dict(r) for r in rows]


# PUBLIC_INTERFACE
def semantic_search_jobs_for_seeker(db: Session, user_id: str, k: int = 20) -> List[Dict[str, Any]]:
    """Stub: Use helper function match_jobs_for_seeker leveraging pgvector similarity."""
    rows = db.execute(
        text(
            """
            select m.job_id, m.similarity, j.title, j.location, j.employment_type, j.is_remote, j.is_published
            from public.match_jobs_for_seeker(:uid, :k) m
            join public.jobs j on j.id = m.job_id
            where j.is_published = true
            order by m.similarity desc
            """
        ),
        {"uid": user_id, "k": k},
    ).mappings().all()
    return [dict(r) for r in rows]
