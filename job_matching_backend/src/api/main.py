from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers.auth import router as auth_router
from src.api.routers.users import router as users_router
from src.api.routers.jobs import router as jobs_router
from src.api.routers.search import router as search_router
from src.api.routers.match import router as match_router
from src.api.routers.integrations import router as integrations_router
from src.api.routers.notifications import router as notifications_router
from src.api.routers.analytics import router as analytics_router
from src.api.routers.admin import router as admin_router
from src.api.routers.cms import router as cms_router
from src.api.routers.jobseekers import router as jobseekers_router
from src.api.routers.employers import router as employers_router
from src.core.config import get_settings, get_cors_origins
from src.core.logging import configure_logging
from src.data.db import health_check as db_health_check

settings = get_settings()
configure_logging()

openapi_tags = [
    {"name": "auth", "description": "Authentication and tokens"},
    {"name": "users", "description": "User profile operations"},
    {"name": "jobs", "description": "Job CRUD and listing"},
    {"name": "search", "description": "Search across jobs"},
    {"name": "match", "description": "Matching recommendations"},
    {"name": "notifications", "description": "Notifications and preferences"},
    {"name": "analytics", "description": "Analytics endpoints"},
    {"name": "admin", "description": "Administrative operations"},
    {"name": "cms", "description": "Content management (news/faq)"},
    {"name": "integrations", "description": "External integrations"},
]

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for the YEP AI-Driven Job Matching Platform. Includes Supabase integration and realtime guidance.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(settings),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["analytics"], summary="Health Check")
def health_check():
    """Return a simple health check status with database connectivity.

    If DATABASE_URL is not configured, the service reports 'degraded' with a message
    to help configure environment variables properly.
    """
    ok = False
    message = None
    try:
        ok = db_health_check()
    except Exception as e:
        message = f"Database not reachable or DATABASE_URL missing: {e}"
        ok = False
    return {"status": "ok" if ok else "degraded", "env": settings.APP_ENV, "message": message}


@app.get("/health", tags=["analytics"], summary="Health Check")
def health_check_endpoint():
    """PUBLIC_INTERFACE
    Health endpoint for uptime probes.

    Returns:
        JSON containing status ("ok" or "degraded"), environment (settings.APP_ENV), and an optional message.
    """
    ok = False
    message = None
    try:
        ok = db_health_check()
    except Exception as e:
        message = f"Database not reachable or DATABASE_URL missing: {e}"
        ok = False
    return {"status": "ok" if ok else "degraded", "env": settings.APP_ENV, "message": message}

@app.get("/api/realtime", tags=["auth"], summary="Realtime WebSocket usage")
def realtime_docs():
    """Realtime usage notes.

    - Client connects to Supabase Realtime with anon/service key depending on context.
    - Use /api/auth/realtime-token/{user_id} to mint a JWT compatible with realtime filters.
    - Subscribe to channels:
      - public:jobs (filter is_published=true)
      - public:applications (employer joins)
      - public:notifications (filter user_id=auth.uid())
      - public:analytics_events (outbox)
    """
    return {
        "channels": [
            "realtime:public:jobs",
            "realtime:public:applications",
            "realtime:public:notifications",
            "realtime:public:analytics_events",
        ],
        "token_endpoint": "/api/auth/realtime-token/{user_id}",
    }

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(jobs_router)
app.include_router(search_router)
app.include_router(match_router)
app.include_router(integrations_router)
app.include_router(notifications_router)
app.include_router(analytics_router)
app.include_router(admin_router)
app.include_router(cms_router)
app.include_router(jobseekers_router)
app.include_router(employers_router)

# ASGI entrypoint note: use `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`
