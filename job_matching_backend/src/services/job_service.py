from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from src.data.repositories.jobs import list_jobs as repo_list_jobs, get_job as repo_get_job, create_job as repo_create_job, update_job as repo_update_job, delete_job as repo_delete_job


# PUBLIC_INTERFACE
def list_jobs(db: Session, q: Optional[str], location: Optional[str], limit: int, offset: int) -> List[Dict[str, Any]]:
    """List published jobs with basic filters."""
    return repo_list_jobs(db, q=q, location=location, limit=limit, offset=offset)


# PUBLIC_INTERFACE
def get_job(db: Session, job_id: str) -> Optional[Dict[str, Any]]:
    """Get a job by id."""
    return repo_get_job(db, job_id)


# PUBLIC_INTERFACE
def create_job(db: Session, employer_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a job for an employer."""
    return repo_create_job(db, employer_id, data)


# PUBLIC_INTERFACE
def update_job(db: Session, job_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing job."""
    return repo_update_job(db, job_id, data)


# PUBLIC_INTERFACE
def delete_job(db: Session, job_id: str) -> bool:
    """Delete a job."""
    return repo_delete_job(db, job_id)
