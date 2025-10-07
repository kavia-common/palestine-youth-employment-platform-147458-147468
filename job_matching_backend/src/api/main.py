from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import re

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
from urllib.parse import urlsplit, parse_qsl

settings = get_settings()
configure_logging()
logger = logging.getLogger("health")

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
_current_cors_origins = get_cors_origins(settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_current_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _effective_sslmode_from_url(db_url: str | None) -> str | None:
    if not db_url:
        return None
    # Try robust parse; if it fails, default to require (our engine normalization enforces it anyway)
    try:
        sp = urlsplit(db_url)
        params = dict(parse_qsl(sp.query, keep_blank_values=True))
        return params.get("sslmode", "require")
    except Exception:
        return "require"

def _dsn_preview(db_url: str | None) -> str | None:
    """Return masked DSN preview for diagnostics."""
    if not db_url:
        return None
    # Prefer regex first to be resilient to special chars in password
    m = re.match(r"^(?P<scheme>postgresql|postgres)(?:\\+[^:]*)?://(?P<user>[^:@/]+):[^@]*@(?P<host>[^/:]+)(?::(?P<port>\\d+))?/(?P<db>[^?]+)", db_url)
    if m:
        scheme = m.group("scheme")
        user = m.group("user")
        host = m.group("host")
        port = m.group("port") or "5432"
        db = m.group("db")
        return f"{scheme}://{user}@{host}:{port}/{db}"
    # Fallback to urlsplit
    try:
        sp = urlsplit(db_url)
        user = sp.username or ""
        host = sp.hostname or ""
        port = sp.port or 5432
        dbname = sp.path.lstrip("/") if sp.path else ""
        scheme = sp.scheme
        scheme = "postgresql" if scheme.startswith("postgresql") else scheme
        return f"{scheme}://{user}@{host}:{port}/{dbname}"
    except Exception:
        return "unparseable"

def _db_scheme(db_url: str | None) -> str | None:
    if not db_url:
        return None
    try:
        sp = urlsplit(db_url)
        return sp.scheme
    except Exception:
        return None

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
        # Avoid implying psycopg2; surface concise message
        message = f"Database not reachable or misconfigured: {str(e)}"
        ok = False
        logger.warning(
            "Health degraded: %s | sslmode=%s",
            message,
            _effective_sslmode_from_url(getattr(settings, "DATABASE_URL", None)),
        )
    db_url = getattr(settings, "DATABASE_URL", None)
    payload = {
        "status": "ok" if ok else "degraded",
        "env": settings.APP_ENV,
        "message": message,
        "sslmode": _effective_sslmode_from_url(db_url),
        "has_database_url": bool(db_url),
        "dsn_preview": _dsn_preview(db_url),
        "db_scheme": _db_scheme(db_url),
    }
    return payload


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
        message = f"Database not reachable or misconfigured: {str(e)}"
        ok = False
        logger.warning(
            "Health degraded: %s | sslmode=%s",
            message,
            _effective_sslmode_from_url(getattr(settings, "DATABASE_URL", None)),
        )
    db_url = getattr(settings, "DATABASE_URL", None)
    payload = {
        "status": "ok" if ok else "degraded",
        "env": settings.APP_ENV,
        "message": message,
        "sslmode": _effective_sslmode_from_url(db_url),
        "has_database_url": bool(db_url),
        "dsn_preview": _dsn_preview(db_url),
        "db_scheme": _db_scheme(db_url),
    }
    return payload

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

@app.get("/api/debug/db-config", tags=["analytics"], summary="Debug DB config (masked)")
def debug_db_config():
    """PUBLIC_INTERFACE
    Debug endpoint to inspect database configuration safely (masked).
    Enabled only when DEBUG_DB_CONFIG=true in environment.

    Returns:
        JSON with:
        - enabled: whether this endpoint is active
        - has_database_url: bool indicating if DATABASE_URL is set
        - dsn_preview: "postgresql://user@host:port/dbname" (password omitted)
        - sslmode: effective sslmode detected from the connection string (after normalization)
    """
    enabled = str(getattr(settings, "DEBUG_DB_CONFIG", "false")).lower() == "true"
    if not enabled:
        return {"enabled": False}

    db_url = settings.DATABASE_URL or ""
    has_database_url = bool(db_url)
    dsn_preview = None
    sslmode = None

    if has_database_url:
        try:
            sp = urlsplit(db_url)
            # mask password in preview
            user = sp.username or ""
            host = sp.hostname or ""
            port = sp.port or 5432
            dbname = sp.path.lstrip("/") if sp.path else ""
            dsn_preview = f"{sp.scheme}://{user}@{host}:{port}/{dbname}"
            params = dict(parse_qsl(sp.query, keep_blank_values=True))
            sslmode = params.get("sslmode", "require")  # db.py enforces require if unspecified
        except Exception:
            dsn_preview = "unparseable"
            sslmode = None

    return {
        "enabled": True,
        "has_database_url": has_database_url,
        "dsn_preview": dsn_preview,
        "sslmode": sslmode,
    }

@app.get("/api/debug/cors", tags=["analytics"], summary="Debug CORS config", description="PUBLIC_INTERFACE\nReturns the currently effective CORS allow_origins list for verification (non-sensitive).")
def debug_cors():
    """Return effective CORS origins list to validate frontend <= backend access."""
    return {"allow_origins": _current_cors_origins}

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
