import os

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    func,
)

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
engine = create_engine(DB_URL, future=True)
md = MetaData()

# Minimal schema used by smoke: meetings + notes
meetings = Table(
    "meetings",
    md,
    Column("id", Integer, primary_key=True),
)

notes = Table(
    "notes",
    md,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("meeting_id", Integer, ForeignKey("meetings.id"), nullable=False),
    Column("content", Text, nullable=False, default=""),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
)


def main():
    # Create tables only if they don't exist
    md.create_all(engine)


if __name__ == "__main__":
    main()
