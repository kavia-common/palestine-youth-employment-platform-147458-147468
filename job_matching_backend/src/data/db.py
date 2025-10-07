from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from sqlalchemy.exc import OperationalError

from src.core.config import get_settings


_engine: Engine | None = None
_SessionLocal = None


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


def _build_engine(normalized_url: str) -> Engine:
    """Create a SQLAlchemy engine with consistent options."""
    return create_engine(
        normalized_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        future=True,
    )


def _ensure_engine() -> Engine:
    """
    Create and cache a global SQLAlchemy engine.

    Notes:
    - Forces SQLAlchemy to use the psycopg v3 driver by rewriting to 'postgresql+psycopg://'
      when the scheme is 'postgres' or 'postgresql'.
    - Enforces 'sslmode=require' by default for Supabase/hosted Postgres unless explicitly set
      in the DATABASE_URL query parameters.
    - Behavior ensures compatibility with Supabase which requires SSL.
    """
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        # Primary URL or raise if not provided
        primary_url = settings.require_database_url()
        # Normalize URL robustly
        primary_norm = _normalize_db_url(primary_url)

        # Attempt primary engine first; if it fails, try DIRECT_URL (if present)
        last_error: Exception | None = None
        for candidate in (primary_norm, _normalize_db_url(settings.DIRECT_URL) if settings.DIRECT_URL else None):
            if not candidate:
                continue
            try:
                eng = _build_engine(candidate)
                # Test connection quickly
                with eng.connect() as conn:
                    conn.execute(text("select 1"))
                _engine = eng
                _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
                break
            except OperationalError as oe:
                last_error = oe
                continue
            except Exception as e:
                last_error = e
                continue

        if _engine is None:
            # Surface the last error for clarity
            if last_error:
                raise last_error
            raise RuntimeError("Failed to initialize database engine: no valid DATABASE_URL/DIRECT_URL candidates")
    return _engine


# PUBLIC_INTERFACE
def get_engine() -> Engine:
    """Return the global SQLAlchemy engine connected to Supabase Postgres."""
    return _ensure_engine()


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
def health_check() -> bool:
    """Perform a light 'select 1' to validate DB connectivity."""
    eng = get_engine()
    with eng.connect() as conn:
        res = conn.execute(text("select 1"))
        _ = res.scalar()
    return True
