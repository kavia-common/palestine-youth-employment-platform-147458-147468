from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.data.db import session_scope
from src.services.notification_service import list_notifications, get_preferences, set_preferences

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class PrefsIn(BaseModel):
    notifications_enabled: Optional[bool] = Field(default=None)
    language: Optional[str] = Field(default=None)
    theme: Optional[str] = Field(default=None)


@router.get("", summary="List notifications")
def notifications(user_id: str, unread_only: bool = False, limit: int = 50):
    """List notifications for a user."""
    with session_scope() as db:
        return list_notifications(db, user_id=user_id, unread_only=unread_only, limit=limit)


@router.get("/preferences", summary="Get notification preferences")
def get_prefs(user_id: str):
    """Get user preferences."""
    with session_scope() as db:
        return get_preferences(db, user_id=user_id)


@router.put("/preferences", summary="Set notification preferences")
def set_prefs(user_id: str, payload: PrefsIn):
    """Set user preferences."""
    with session_scope() as db:
        return set_preferences(db, user_id=user_id, notifications_enabled=payload.notifications_enabled, language=payload.language, theme=payload.theme)
