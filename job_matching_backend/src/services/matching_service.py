from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.orm import Session


# PUBLIC_INTERFACE
def basic_match_for_seeker(db: Session, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Simple matching stub based on location and keywords until embeddings are available."""
    # Using simple heuristic: same location, published jobs ordered by posted_at
    rows = db.execute(
        text(
            """
            with seeker as (
                select location, desired_role from public.job_seekers where user_id = :uid
            )
            select j.id, j.title, j.location, j.posted_at
            from public.jobs j, seeker s
            where j.is_published = true
              and (s.location is null or j.location = s.location)
              and (s.desired_role is null or j.title ilike '%' || s.desired_role || '%')
            order by j.posted_at desc
            limit :limit
            """
        ),
        {"uid": user_id, "limit": limit},
    ).mappings().all()
    return [dict(r) for r in rows]
