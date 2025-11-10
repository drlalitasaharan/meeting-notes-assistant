from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Make "app" importable (backend/ is parent of alembic/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import models' Base for autogenerate & target_metadata
from app.models import Base  # noqa: E402

# Alembic Config object
config = context.config

# Logging
if config.config_file_name:
    fileConfig(config.config_file_name)

# Let Alembic see our metadata
target_metadata = Base.metadata


def get_db_url() -> str:
    # Priority: explicit var for Alembic -> generic DATABASE_URL -> dev sqlite
    return (
        os.getenv("ALEMBIC_DB_URL") or os.getenv("DATABASE_URL") or "sqlite:////app/backend/dev.db"
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    cfg = config.get_section(config.config_ini_section) or {}
    cfg["sqlalchemy.url"] = get_db_url()

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
