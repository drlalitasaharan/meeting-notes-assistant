from __future__ import annotations

import enum

from sqlalchemy import Column, DateTime, Enum, Index, Integer, String, Text, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True)  # UUID
    job_type = Column(String(64), nullable=False)
    input_hash = Column(String(64), nullable=False)  # sha256
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.queued)
    retries = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    artifact_key = Column(String(512), nullable=True)
    rq_job_id = Column(String(64), nullable=True)
    error = Column(Text, nullable=True)
    trace_id = Column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_created_at", "created_at"),
        Index("uq_jobs_type_inputhash", "job_type", "input_hash", unique=True),
    )
