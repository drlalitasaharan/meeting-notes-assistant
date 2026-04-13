from __future__ import annotations

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, func

from app.models import Base


class MeetingNotes(Base):
    __tablename__ = "meeting_notes"

    id = Column(Integer, primary_key=True)
    meeting_id = Column(
        Integer,
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
    )

    raw_transcript = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    summary_slots = Column(JSON, nullable=True)

    key_points = Column(JSON, nullable=True)

    action_items = Column(JSON, nullable=True)
    action_item_objects = Column(JSON, nullable=True)

    decisions = Column(JSON, nullable=True)
    decision_objects = Column(JSON, nullable=True)

    model_version = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
