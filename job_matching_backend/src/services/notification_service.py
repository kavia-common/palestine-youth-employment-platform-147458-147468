from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session


# PUBLIC_INTERFACE
def list_notifications(db: Session, user_id: str, unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
    """List user's notifications."""
    sql = """
        select id, user_id, type, title, body, read_at, created_at
        from public.notifications
        where user_id = :uid
    """
    if unread_only:
        sql += " and read_at is null"
    sql += " order by created_at desc limit :limit"
    rows = db.execute(text(sql), {"uid": user_id, "limit": limit}).mappings().all()
    return [dict(r) for r in rows]


# PUBLIC_INTERFACE
def get_preferences(db: Session, user_id: str) -> Dict[str, Any]:
    """Get user preferences."""
    row = db.execute(
        text("select user_id, notifications_enabled, language, theme from public.preferences where user_id = :uid"),
        {"uid": user_id},
    ).mappings().first()
    return dict(row) if row else {"user_id": user_id, "notifications_enabled": True, "language": "en", "theme": "system"}


# PUBLIC_INTERFACE
def set_preferences(db: Session, user_id: str, notifications_enabled: Optional[bool], language: Optional[str], theme: Optional[str]) -> Dict[str, Any]:
    """Upsert preferences."""
    row = db.execute(
        text(
            """
            insert into public.preferences (user_id, notifications_enabled, language, theme)
            values (:uid, coalesce(:ne, true), coalesce(:lang, 'en'), coalesce(:theme, 'system'))
            on conflict (user_id)
            do update set notifications_enabled = coalesce(excluded.notifications_enabled, public.preferences.notifications_enabled),
                          language = coalesce(excluded.language, public.preferences.language),
                          theme = coalesce(excluded.theme, public.preferences.theme)
            returning user_id, notifications_enabled, language, theme
            """
        ),
        {"uid": user_id, "ne": notifications_enabled, "lang": language, "theme": theme},
    ).mappings().first()
    return dict(row)  # type: ignore
