from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from src.core.config import get_settings


_engine: Engine | None = None
_SessionLocal = None


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
        # Validate DB URL with helpful message if missing
        db_url = settings.require_database_url()

        try:
            sp = urlsplit(db_url)
            scheme = sp.scheme
            # Normalize postgres scheme and pin to psycopg v3 driver
            # Accept 'postgres://' or 'postgresql://' and convert to 'postgresql+psycopg://'
            if scheme in ("postgres", "postgresql"):
                driver_scheme = "postgresql+psycopg"
                query_pairs = dict(parse_qsl(sp.query, keep_blank_values=True))
                # Only set if not already provided
                if "sslmode" not in query_pairs:
                    query_pairs["sslmode"] = "require"
                new_query = urlencode(query_pairs)

                # Rebuild URL with explicit driver
                # urlunsplit expects (scheme, netloc, path, query, fragment)
                normalized_url = urlunsplit((driver_scheme, sp.netloc, sp.path, new_query, sp.fragment))
                db_url = normalized_url
            else:
                # If a custom SQLAlchemy URL was provided without driver, leave it as-is
                # but it should already include a working driver.
                pass
        except Exception:
            # If parsing fails, continue with original URL; engine may still handle it.
            pass

        # SQLAlchemy 2.0 style engine using psycopg v3 driver
        _engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            future=True,
        )
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
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
