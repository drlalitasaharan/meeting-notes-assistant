from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class MeetingFeedback(Base):
    __tablename__ = "meeting_feedback"
    __table_args__ = (
        UniqueConstraint("user_id", "meeting_id", name="uq_meeting_feedback_user_meeting"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    usefulness: Mapped[str] = mapped_column(String(20), nullable=False)
    most_useful: Mapped[str] = mapped_column(String(40), nullable=False)
    improvement_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    would_use_again: Mapped[str] = mapped_column(String(20), nullable=False)
    meeting_type: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=func.now(),
    )
