from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from src.core.config import get_settings


_engine: Engine | None = None
_SessionLocal = None


def _ensure_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        # SQLAlchemy 2.0 style engine
        _engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10, future=True)
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
