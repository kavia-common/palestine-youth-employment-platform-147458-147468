from typing import Optional, List

from src.core.security import create_supabase_realtime_jwt


# PUBLIC_INTERFACE
def mint_realtime_token(user_id: str, channels: Optional[List[str]] = None, minutes: int = 60) -> str:
    """Mint a realtime JWT for a specific user id to use with Supabase Realtime client."""
    return create_supabase_realtime_jwt(subject=user_id, role="authenticated", channels=channels or [], expires_minutes=minutes)
