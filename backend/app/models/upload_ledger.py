from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class UploadLedger(Base):
    __tablename__ = "upload_ledger"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    meeting_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    original_filename: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    storage_key: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="started", server_default="started"
    )
    counted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
