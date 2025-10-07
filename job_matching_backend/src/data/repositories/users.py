from typing import Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session


# PUBLIC_INTERFACE
def get_user_by_id(db: Session, user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a user by id from public.users"""
    row = db.execute(
        text("select id, email, user_type, full_name, phone, avatar_url, created_at, updated_at from public.users where id = :id"),
        {"id": user_id},
    ).mappings().first()
    return dict(row) if row else None


# PUBLIC_INTERFACE
def get_user_by_email(db: Session, email: str) -> Optional[Dict[str, Any]]:
    """Fetch a user by email from public.users"""
    row = db.execute(
        text("select id, email, user_type, full_name, phone, avatar_url, created_at, updated_at from public.users where email = :email"),
        {"email": email},
    ).mappings().first()
    return dict(row) if row else None


# PUBLIC_INTERFACE
def create_user(db: Session, user_id: str, email: str, user_type: str, full_name: Optional[str] = None) -> Dict[str, Any]:
    """Insert a new user into public.users (id should match auth.users id in Supabase)."""
    db.execute(
        text(
            """
            insert into public.users (id, email, user_type, full_name)
            values (:id, :email, :user_type, :full_name)
            on conflict (id) do update set email = excluded.email, user_type = excluded.user_type, full_name = excluded.full_name
            """
        ),
        {"id": user_id, "email": email, "user_type": user_type, "full_name": full_name},
    )
    row = db.execute(
        text("select id, email, user_type, full_name, phone, avatar_url, created_at, updated_at from public.users where id = :id"),
        {"id": user_id},
    ).mappings().first()
    return dict(row) if row else {"id": user_id, "email": email, "user_type": user_type, "full_name": full_name}
