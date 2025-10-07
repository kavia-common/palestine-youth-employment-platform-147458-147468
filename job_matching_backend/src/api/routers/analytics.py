from fastapi import APIRouter
from sqlalchemy import text

from src.data.db import session_scope

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/counts", summary="Basic counts")
def counts():
    """Return basic system counts useful for dashboard."""
    with session_scope() as db:
        users = db.execute(text("select count(*) from public.users")).scalar()
        jobs = db.execute(text("select count(*) from public.jobs")).scalar()
        applications = db.execute(text("select count(*) from public.applications")).scalar()
        return {"users": int(users or 0), "jobs": int(jobs or 0), "applications": int(applications or 0)}
