"""
Lightweight Additive Schema Sync

This project has no Alembic migration history yet (`backend/migrations`
only holds the scaffold) — the whole schema is managed by
`Base.metadata.create_all()`, which creates missing tables but never alters
existing ones. That's fine until a column gets added to an ORM model after
a database file already exists with the old shape, which is exactly what
happens the first time this runs against the already-seeded dev database.

Rather than require a manual `ALTER TABLE` or a full Alembic migration for
one nullable column, this does the minimal safe thing at startup: for each
declared model, diff its mapped columns against what the live table
actually has, and `ADD COLUMN` whatever's missing. Never drops, renames, or
alters an existing column — additive only, safe to run every boot.
"""
from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from backend.app.core.logging import logger
from backend.app.database.session import Base


def _column_ddl_type(column) -> str:
    """SQLite/Postgres both accept these standard type names for ADD COLUMN."""
    return column.type.compile(dialect=None) if hasattr(column.type, "compile") else str(column.type)


def sync_additive_columns(engine: Engine) -> None:
    """Create any missing tables, then add any missing nullable columns on
    existing tables. Safe to call on every application startup."""
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.connect() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue  # just created above, already has every column

            existing_columns = {col["name"] for col in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns:
                    continue
                if not column.nullable and column.default is None:
                    # Can't safely backfill a NOT NULL column with no default
                    # on rows that already exist — skip and log instead of
                    # guessing a value.
                    logger.warning(
                        f"schema_sync: {table.name}.{column.name} is missing but NOT NULL "
                        "with no default — skipping automatic add; needs a real migration."
                    )
                    continue

                ddl_type = _column_ddl_type(column)
                try:
                    conn.execute(text(f"ALTER TABLE {table.name} ADD COLUMN {column.name} {ddl_type}"))
                    conn.commit()
                    logger.info(f"schema_sync: added {table.name}.{column.name} ({ddl_type})")
                except Exception as exc:
                    logger.warning(f"schema_sync: could not add {table.name}.{column.name}: {exc}")
