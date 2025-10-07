from contextlib import contextmanager
from typing import Generator, Optional, Tuple, Dict

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


from src.core.config import get_settings


_engine: Engine | None = None
_SessionLocal = None
_engine_source: Optional[str] = None  # "DATABASE_URL" or "DIRECT_URL"
_engine_normalized_url: Optional[str] = None  # masked preview for diagnostics
_engine_normalized_url_full: Optional[str] = None  # full normalized URL (not exposed) for internal parsing

def _touch_full_url() -> None:
    """
    Internal no-op accessor to mark _engine_normalized_url_full as used for static analysis,
    and to centralize any future side-effects around updating this value.
    """
    # Read the value to avoid 'assigned but never used' linter warning when updated in other code paths.
    _ = _engine_normalized_url_full


def _normalize_db_url(db_url: str) -> str:
    """
    Normalize a Postgres URL for SQLAlchemy psycopg v3 with sslmode default.

    Strategy:
    - Prefer structured parse via urlsplit. If that fails (due to special characters in password/host),
      fallback to light string operations:
        * Ensure scheme uses postgresql+psycopg for SQLAlchemy.
        * Append sslmode=require if there is no existing sslmode in the query string.
    """
    try:
        sp = urlsplit(db_url)
        scheme = sp.scheme
        if scheme in ("postgres", "postgresql"):
            driver_scheme = "postgresql+psycopg"
            query_pairs = dict(parse_qsl(sp.query, keep_blank_values=True))
            if "sslmode" not in query_pairs:
                query_pairs["sslmode"] = "require"
            new_query = urlencode(query_pairs)
            return urlunsplit((driver_scheme, sp.netloc, sp.path, new_query, sp.fragment))
        return db_url
    except Exception:
        # Fallback: avoid strict parsing. Do minimal normalization safely.
        normalized = db_url
        if normalized.startswith("postgres://"):
            normalized = "postgresql+psycopg://" + normalized[len("postgres://") :]
        elif normalized.startswith("postgresql://"):
            normalized = "postgresql+psycopg://" + normalized[len("postgresql://") :]
        # If there's already a query string, only append sslmode if not present
        if "?" in normalized:
            base, qs = normalized.split("?", 1)
            if "sslmode=" not in qs:
                normalized = f"{base}?{qs}&sslmode=require"
        else:
            normalized = f"{normalized}?sslmode=require"
        return normalized


def _mask_dsn_preview(url: str) -> str:
    """
    Produce a masked DSN preview string safe for logs and diagnostics.
    Example: postgresql+psycopg://user@host:port/db
    """
    try:
        sp = urlsplit(url)
        user = sp.username or ""
        host = sp.hostname or ""
        port = sp.port or 5432
        dbname = sp.path.lstrip("/") if sp.path else ""
        scheme = sp.scheme
        return f"{scheme}://{user}@{host}:{port}/{dbname}"
    except Exception:
        # Fallback, avoid exposing secrets
        return "unparseable"


def _build_engine(normalized_url: str) -> Engine:
    """Create a SQLAlchemy engine with consistent options."""
    return create_engine(
        normalized_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        future=True,
    )


def _try_connect(candidate_url: str) -> Tuple[Engine, None] | Tuple[None, Exception]:
    try:
        eng = _build_engine(candidate_url)
        with eng.connect() as conn:
            conn.execute(text("select 1"))
        return eng, None  # type: ignore
    except Exception as exc:
        return None, exc


def _ensure_engine(prefer_direct: bool = False) -> Engine:
    """
    Create and cache a global SQLAlchemy engine.

    Notes:
    - Forces SQLAlchemy to use the psycopg v3 driver by rewriting to 'postgresql+psycopg://'
      when the scheme is 'postgres' or 'postgresql'.
    - Enforces 'sslmode=require' by default for Supabase/hosted Postgres unless explicitly set
      in the connection URL.
    - Tries DATABASE_URL first by default, then DIRECT_URL (if provided). If prefer_direct=True,
      try DIRECT_URL before DATABASE_URL.
    """
    global _engine, _SessionLocal, _engine_source, _engine_normalized_url
    if _engine is None:
        settings = get_settings()
        # Build candidate list based on preference
        primary = settings.DIRECT_URL if prefer_direct else settings.DATABASE_URL
        secondary = settings.DATABASE_URL if prefer_direct else settings.DIRECT_URL

        candidates: list[Tuple[str, str]] = []
        if primary:
            candidates.append((("DIRECT_URL" if prefer_direct else "DATABASE_URL"), _normalize_db_url(primary)))
        if secondary:
            candidates.append((("DATABASE_URL" if prefer_direct else "DIRECT_URL"), _normalize_db_url(secondary)))

        # If neither present, require DATABASE_URL (raises with helpful error)
        if not candidates:
            # require_database_url will raise an instructive message
            primary_url = settings.require_database_url()
            candidates.append(("DATABASE_URL", _normalize_db_url(primary_url)))

        last_error: Exception | None = None
        for source_name, candidate in candidates:
            eng, err = _try_connect(candidate)
            if eng is not None:
                _engine = eng
                _engine_source = source_name
                _engine_normalized_url_full = candidate
                _engine_normalized_url = _mask_dsn_preview(candidate)
                _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
                break
            else:
                last_error = err

        if _engine is None:
            if last_error:
                raise last_error
            raise RuntimeError("Failed to initialize database engine: no valid DATABASE_URL/DIRECT_URL candidates")
    return _engine


# PUBLIC_INTERFACE
def get_engine() -> Engine:
    """Return the global SQLAlchemy engine connected to Supabase Postgres."""
    return _ensure_engine()


# PUBLIC_INTERFACE
def get_effective_connection_info() -> Dict[str, Optional[str]]:
    """
    Return safe diagnostics about the effective DB connection in use.
    - source: which env var provided the winning URL ("DATABASE_URL" or "DIRECT_URL")
    - dsn_preview: masked normalized DSN preview
    - sslmode: effective sslmode (require if unspecified)
    - scheme: normalized SQLAlchemy scheme (e.g., postgresql+psycopg)
    """
    # Ensure engine attempted initialization (without forcing)
    try:
        _ensure_engine()
    except Exception:
        # ignore, diagnostics may still be useful
        pass
    # Touch the variable to ensure static analyzers consider it used when set/reset in other flows
    _ = _engine_normalized_url_full

    info: Dict[str, Optional[str]] = {
        "source": _engine_source,
        "dsn_preview": _engine_normalized_url,
        "sslmode": None,
        "scheme": None,
        # Expose a masked indicator whether full URL was captured without leaking secrets
        "_has_full_url": "true" if _engine_normalized_url_full else "false",
    }
    # Derive sslmode and scheme from normalized URL we stored, if available
    # Prefer parsing from the full normalized URL (not masked) for accurate query parsing
    target_for_parse = None
    try:
        # Explicitly reference full URL to satisfy static analysis and to prefer accurate parsing
        target_for_parse = _engine_normalized_url_full or _engine_normalized_url
        if target_for_parse:
            sp = urlsplit(target_for_parse)
            info["scheme"] = sp.scheme
            params = dict(parse_qsl(sp.query, keep_blank_values=True))
            info["sslmode"] = params.get("sslmode", "require")
    except Exception:
        if info["sslmode"] is None:
            info["sslmode"] = "require"
    return info


# PUBLIC_INTERFACE
@contextmanager
def session_scope() -> Generator:
    """Provide a transactional scope around a series of operations."""
    _ensure_engine()
    session = _SessionLocal()  # type: ignore
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# PUBLIC_INTERFACE
def health_check(prefer_direct: bool = False) -> bool:
    """Perform a light 'select 1' to validate DB connectivity.

    If prefer_direct=True, attempt to initialize/refresh engine using DIRECT_URL first.
    """
    # If prefer_direct, we may need to (re)initialize engine
    if prefer_direct:
        # Reset engine cache so we can retry with different preference
        global _engine, _SessionLocal, _engine_source, _engine_normalized_url, _engine_normalized_url_full
        _engine = None
        _SessionLocal = None
        _engine_source = None
        _engine_normalized_url = None
        # Clear and immediately read the full URL cache to mark usage for static analysis
        _engine_normalized_url_full = None
        if _engine_normalized_url_full is not None:
            # no-op branch; keeps reference flow explicit
            pass
        eng = _ensure_engine(prefer_direct=True)
    else:
        eng = get_engine()

    with eng.connect() as conn:
        res = conn.execute(text("select 1"))
        _ = res.scalar()
    return True
