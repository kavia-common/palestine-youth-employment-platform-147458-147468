from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session


# PUBLIC_INTERFACE
def list_jobs(db: Session, q: Optional[str] = None, location: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """List published jobs with optional filters."""
    base = """
        select j.id, j.title, j.description, j.location, j.employment_type, j.salary_min, j.salary_max,
               j.currency, j.is_remote, j.is_published, j.posted_at, j.expires_at, e.org_name as employer_name
        from public.jobs j
        join public.employers e on e.user_id = j.employer_id
        where j.is_published = true
    """
    params: Dict[str, Any] = {}
    if q:
        base += " and (j.title ilike :q or j.description ilike :q)"
        params["q"] = f"%{q}%"
    if location:
        base += " and j.location = :location"
        params["location"] = location
    base += " order by j.posted_at desc limit :limit offset :offset"
    params["limit"] = limit
    params["offset"] = offset

    rows = db.execute(text(base), params).mappings().all()
    return [dict(r) for r in rows]


# PUBLIC_INTERFACE
def get_job(db: Session, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a single job by id."""
    row = db.execute(
        text(
            """
            select j.*, e.org_name as employer_name
            from public.jobs j
            join public.employers e on e.user_id = j.employer_id
            where j.id = :id
            """
        ),
        {"id": job_id},
    ).mappings().first()
    return dict(row) if row else None


# PUBLIC_INTERFACE
def create_job(db: Session, employer_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a job owned by the employer (RLS enforces employer_id = auth.uid() when using PostgREST/Supabase)."""
    insert_sql = """
        insert into public.jobs (employer_id, title, description, location, employment_type,
                                 salary_min, salary_max, currency, is_remote, is_published, expires_at)
        values (:employer_id, :title, :description, :location, :employment_type, :salary_min, :salary_max,
                :currency, :is_remote, :is_published, :expires_at)
        returning *
    """
    row = db.execute(text(insert_sql), {"employer_id": employer_id, **data}).mappings().first()
    return dict(row)  # type: ignore


# PUBLIC_INTERFACE
def update_job(db: Session, job_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a job. RLS: only employer owner or admin can update."""
    set_cols = []
    params: Dict[str, Any] = {"id": job_id}
    for k, v in data.items():
        set_cols.append(f"{k} = :{k}")
        params[k] = v
    if not set_cols:
        return get_job(db, job_id)
    sql = f"update public.jobs set {', '.join(set_cols)} where id = :id returning *"
    row = db.execute(text(sql), params).mappings().first()
    return dict(row) if row else None


# PUBLIC_INTERFACE
def delete_job(db: Session, job_id: str) -> bool:
    """Delete a job. RLS applies."""
    res = db.execute(text("delete from public.jobs where id = :id"), {"id": job_id})
    return res.rowcount > 0
