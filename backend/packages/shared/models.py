from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime

class Base(DeclarativeBase):
    pass

class Meeting(Base):
    __tablename__ = "meetings"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="new")   # new|processing|done|failed
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)    # CSV: "sprint,planning"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @property
    def tags_list(self) -> list[str]:
        return [t.strip() for t in (self.tags or "").split(",") if t.strip()]
