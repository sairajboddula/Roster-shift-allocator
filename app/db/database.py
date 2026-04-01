"""Database engine, session factory, and init utilities."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Render's free PostgreSQL uses "postgres://" but SQLAlchemy 2.x requires "postgresql://"
_db_url = settings.DATABASE_URL.replace("postgres://", "postgresql://", 1)
_is_sqlite = _db_url.startswith("sqlite")

_engine_kwargs: dict = {"echo": settings.DB_ECHO}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(_db_url, **_engine_kwargs)

if _is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def init_db() -> None:
    """Create all tables in the database."""
    # Import all models so Base.metadata is populated
    from app.models import employee, department, shift, schedule, history, feedback, user  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialised: all tables created.")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
