from __future__ import with_statement
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
import os
import sys

# Add backend/ and backend/app to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_DIR = os.path.join(BASE_DIR, "app")
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
if APP_DIR not in sys.path:
    sys.path.append(APP_DIR)

# Alembic Config object
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import settings and models from shared package
from packages.shared.env import get_settings
from packages.shared.models import Base

target_metadata = Base.metadata


def get_url():
    s = get_settings()
    return s.DATABASE_URL


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        {"sqlalchemy.url": get_url()},
        prefix="sqlalchemy.",         # <-- key fix: match sqlalchemy.url
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

