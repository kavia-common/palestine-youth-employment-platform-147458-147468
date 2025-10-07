from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.data.db import session_scope
from src.services.job_service import list_jobs as svc_list_jobs, get_job as svc_get_job, create_job as svc_create_job, update_job as svc_update_job, delete_job as svc_delete_job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobIn(BaseModel):
    title: str = Field(..., description="Job title")
    description: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    employment_type: Optional[str] = Field(default=None)
    salary_min: Optional[float] = Field(default=None)
    salary_max: Optional[float] = Field(default=None)
    currency: Optional[str] = Field(default=None)
    is_remote: Optional[bool] = Field(default=False)
    is_published: Optional[bool] = Field(default=False)
    expires_at: Optional[str] = Field(default=None, description="ISO datetime string")


@router.get("", summary="List jobs")
def list_jobs(q: Optional[str] = None, location: Optional[str] = None, limit: int = 20, offset: int = 0):
    """List published jobs with optional filters."""
    with session_scope() as db:
        return svc_list_jobs(db, q=q, location=location, limit=limit, offset=offset)


@router.get("/{job_id}", summary="Get job by id")
def get_job(job_id: str):
    """Fetch a single job."""
    with session_scope() as db:
        job = svc_get_job(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job


@router.post("", summary="Create job")
def create_job(employer_id: str, payload: JobIn):
    """Create a job owned by employer_id."""
    with session_scope() as db:
        job = svc_create_job(db, employer_id=employer_id, data=payload.model_dump())
        return job


@router.put("/{job_id}", summary="Update job")
def update_job(job_id: str, payload: JobIn):
    """Update job fields."""
    with session_scope() as db:
        job = svc_update_job(db, job_id=job_id, data=payload.model_dump(exclude_unset=True))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found or not permitted")
        return job


@router.delete("/{job_id}", summary="Delete job")
def delete_job(job_id: str):
    """Delete a job."""
    with session_scope() as db:
        ok = svc_delete_job(db, job_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Job not found or not permitted")
        return {"ok": ok}
