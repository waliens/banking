from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session_factory(engine_instance: Engine | None = None) -> sessionmaker[Session]:
    """Create a session factory for a given engine. Used by tests to swap in a test DB."""
    if engine_instance is None:
        engine_instance = engine
    return sessionmaker(bind=engine_instance, autoflush=False, expire_on_commit=False)
