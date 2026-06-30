from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if TYPE_CHECKING:
    from app.models.user import User


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    agenda: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user: Mapped["User"] = relationship("User", back_populates="meetings")

    raw_media_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    media_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    media_content_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    media_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    confidential_mode: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )
    recording_retention_policy: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    recording_deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recording_delete_status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="not_required",
        server_default="not_required",
        index=True,
    )
    recording_delete_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    last_error: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    processing_stage: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    processing_error_code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    processing_error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    processing_diagnostics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    processing_timings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="new", server_default="new"
    )
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

    @property
    def processing_progress_label(self) -> str:
        labels = {
            "uploaded": "Upload received",
            "validating_media": "Checking the recording",
            "processing_audio": "Preparing audio",
            "transcribing": "Transcribing audio",
            "generating_notes": "Generating notes",
            "finalizing": "Finalizing notes",
            "completed": "Notes ready",
            "failed": "Processing failed",
        }
        return labels.get((self.processing_stage or "").strip().lower(), "Processing")
