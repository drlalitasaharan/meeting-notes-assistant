from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.jobs import process_meeting
from app.models import Base
from app.models.meeting import Meeting


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_meeting(
    db: Session,
    *,
    confidential_mode: bool,
    raw_media_path: str | None = "raw_media/test-recording.m4a",
) -> Meeting:
    meeting = Meeting(
        title="Confidential test meeting",
        raw_media_path=raw_media_path,
        confidential_mode=confidential_mode,
        recording_retention_policy="delete_after_notes" if confidential_mode else "standard",
        recording_delete_status="pending" if confidential_mode else "not_required",
        status="done",
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def test_confidential_recording_delete_marks_deleted(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    meeting = _create_meeting(db_session, confidential_mode=True)
    deleted_paths: list[str | None] = []

    monkeypatch.setattr(
        process_meeting,
        "delete_raw_media_best_effort",
        lambda raw_media_path: deleted_paths.append(raw_media_path) or True,
    )

    process_meeting._finalize_confidential_recording_delete(
        db=db_session,
        meeting=meeting,
        raw_media_path=meeting.raw_media_path,
        log_extra={"meeting_id": meeting.id},
    )

    db_session.refresh(meeting)

    assert deleted_paths == ["raw_media/test-recording.m4a"]
    assert meeting.recording_delete_status == "deleted"
    assert meeting.recording_deleted_at is not None
    assert meeting.recording_delete_error is None


def test_non_confidential_recording_is_not_deleted(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    meeting = _create_meeting(db_session, confidential_mode=False)

    monkeypatch.setattr(
        process_meeting,
        "delete_raw_media_best_effort",
        lambda raw_media_path: pytest.fail("delete should not be called"),
    )

    process_meeting._finalize_confidential_recording_delete(
        db=db_session,
        meeting=meeting,
        raw_media_path=meeting.raw_media_path,
        log_extra={"meeting_id": meeting.id},
    )

    db_session.refresh(meeting)

    assert meeting.recording_delete_status == "not_required"
    assert meeting.recording_deleted_at is None
    assert meeting.recording_delete_error is None


def test_confidential_recording_delete_failure_does_not_raise(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    meeting = _create_meeting(db_session, confidential_mode=True)

    monkeypatch.setattr(
        process_meeting,
        "delete_raw_media_best_effort",
        lambda raw_media_path: False,
    )

    process_meeting._finalize_confidential_recording_delete(
        db=db_session,
        meeting=meeting,
        raw_media_path=meeting.raw_media_path,
        log_extra={"meeting_id": meeting.id},
    )

    db_session.refresh(meeting)

    assert meeting.recording_delete_status == "failed"
    assert meeting.recording_deleted_at is None
    assert meeting.recording_delete_error == "Recording deletion did not complete."
