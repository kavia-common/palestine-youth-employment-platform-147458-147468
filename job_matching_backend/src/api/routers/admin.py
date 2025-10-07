from fastapi import APIRouter
from sqlalchemy import text

from src.data.db import session_scope

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.put("/users/{user_id}/role", summary="Update user role")
def update_user_role(user_id: str, user_type: str):
    """Update user role (requires admin - enforced by auth in production)."""
    with session_scope() as db:
        db.execute(text("update public.users set user_type = :t where id = :id"), {"t": user_type, "id": user_id})
        return {"id": user_id, "user_type": user_type}


@router.get("/audit-logs", summary="List audit logs (stub)")
def audit_logs(limit: int = 50):
    """Stub for audit logs listing."""
    with session_scope() as db:
        rows = db.execute(text("select id, actor_id, action, entity, entity_id, created_at from public.audit_logs order by created_at desc limit :l"), {"l": limit}).mappings().all()
        return [dict(r) for r in rows]
