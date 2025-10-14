from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Re-export model classes (after Base is defined)
from .meeting import Meeting as Meeting  # noqa: E402
from .note import Note as Note  # noqa: E402

__all__ = ["Base", "Meeting", "Note"]
