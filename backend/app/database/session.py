"""
SQLAlchemy 2.0 Database Session & Base Model Configuration
"""
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Generator
from sqlalchemy import DateTime, String, create_engine
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from backend.app.core.config import settings


class Base(DeclarativeBase):
    """
    Abstract declarative base entity with UUID primary keys and audit timestamps
    """
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = str(uuid.uuid4())
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.now(timezone.utc)
        if "updated_at" not in kwargs:
            kwargs["updated_at"] = datetime.now(timezone.utc)
        if hasattr(self, "__table__"):
            for col in self.__table__.columns:
                if col.name not in kwargs and col.default is not None:
                    if callable(col.default.arg):
                        kwargs[col.name] = col.default.arg(None)
                    else:
                        kwargs[col.name] = col.default.arg
        for k, v in kwargs.items():
            setattr(self, k, v)



# Synchronous engine for Alembic and worker routines
sync_database_url = settings.DATABASE_URL
if sync_database_url.startswith("postgresql+psycopg://"):
    pass
elif sync_database_url.startswith("postgresql://"):
    sync_database_url = sync_database_url.replace("postgresql://", "postgresql+psycopg://", 1)

# SQLite fallback compatibility for testing environments
if "sqlite" in sync_database_url:
    engine = create_engine(sync_database_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        sync_database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Any, None, None]:
    """Dependency for obtaining synchronous database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
