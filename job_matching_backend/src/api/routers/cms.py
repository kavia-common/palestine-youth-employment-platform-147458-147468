from fastapi import APIRouter
from sqlalchemy import text

from src.data.db import session_scope

router = APIRouter(prefix="/api/cms", tags=["cms"])


@router.get("/news", summary="List published news")
def news(limit: int = 20):
    """List published news."""
    with session_scope() as db:
        rows = db.execute(
            text("select id, title, body, published_at from public.cms_news where published = true order by published_at desc nulls last limit :l"),
            {"l": limit},
        ).mappings().all()
        return [dict(r) for r in rows]


@router.get("/faq", summary="List published FAQ")
def faq():
    """List published FAQ."""
    with session_scope() as db:
        rows = db.execute(
            text("select id, question, answer, order_index from public.cms_faq where published = true order by order_index asc"),
        ).mappings().all()
        return [dict(r) for r in rows]
