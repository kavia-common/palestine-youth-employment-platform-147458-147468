from fastapi import APIRouter

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/partners", summary="List integration partners (stub)")
def partners():
    """Stub: list partners - replace with DB-backed list."""
    return [{"id": "stub", "name": "Partner A", "enabled": True}]
