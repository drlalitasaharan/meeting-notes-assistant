# backend/init_db.py
"""
Initialize database schema.

- Uses the app's configured SQLAlchemy engine
- Structured logging (no prints)
"""

from app.core.logger import get_logger
from app.core.db import engine
from packages.shared.models import Base

log = get_logger(__name__)


def main() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        log.info("✅ Database tables created successfully")
    except Exception:
        log.exception("Database initialization failed")
        raise


if __name__ == "__main__":
    main()

