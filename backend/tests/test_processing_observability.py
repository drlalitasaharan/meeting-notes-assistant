from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.deps import get_current_user
from app.models import Base
from app.models.meeting import Meeting
from app.models.meeting_notes import MeetingNotes
from app.models.user import User
from app.routers import admin, meeting_notes_api, meetings
from app.services.processing_observability import (
    begin_attempt,
    mark_completed,
    mark_failed,
    mark_stage,
)


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


def _create_user(db: Session, email: str = "owner@example.com") -> User:
    user = User(
        email=email,
        password_hash="not-used-in-test",
        first_name="Test",
        last_name="User",
        organization_name="Test Org",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_meeting(db: Session, *, user_id: int, status: str = "PROCESSING") -> Meeting:
    meeting = Meeting(
        title="Processing visibility",
        user_id=user_id,
        raw_media_path="/private/tmp/raw-meeting.mp3",
        status=status,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def test_stage_helper_records_idempotent_timings_and_completed_timestamp(
    db_session: Session,
) -> None:
    user = _create_user(db_session)
    meeting = _create_meeting(db_session, user_id=user.id)

    begin_attempt(meeting)
    first_started_at = meeting.processing_timings["media_validation_started_at"]
    mark_stage(meeting, "validating_media", started_key="media_validation_started_at")
    mark_completed(meeting)

    assert meeting.status == "DONE"
    assert meeting.processing_stage == "completed"
    assert meeting.processing_attempts == 1
    assert meeting.processing_timings["media_validation_started_at"] == first_started_at
    assert "processing_completed_at" in meeting.processing_timings


def test_failed_job_stores_safe_user_message_and_sanitized_diagnostic(
    db_session: Session,
) -> None:
    user = _create_user(db_session)
    meeting = _create_meeting(db_session, user_id=user.id)
    exc = RuntimeError("Provider failed api_key=secret-token at /Users/example/private/audio.mp3")

    mark_failed(meeting, exc, stage="generating_notes")

    assert meeting.status == "ERROR"
    assert meeting.processing_stage == "failed"
    assert meeting.processing_error_code == "processing_failed"
    assert meeting.processing_error_message == (
        "We could not process this recording. Please check the file format and try again."
    )
    assert meeting.last_error == meeting.processing_error_message
    assert "secret-token" not in (meeting.processing_diagnostics or "")
    assert "/Users/example" not in (meeting.processing_diagnostics or "")
    assert "processing_failed_at" in meeting.processing_timings


def test_meeting_api_keeps_status_and_adds_progress_metadata(db_session: Session) -> None:
    user = _create_user(db_session)
    meeting = _create_meeting(db_session, user_id=user.id)
    mark_stage(meeting, "transcribing", status="PROCESSING")
    db_session.add(meeting)
    db_session.commit()

    app = FastAPI()
    app.include_router(meetings.router)

    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[meetings.get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user

    response = TestClient(app).get(f"/v1/meetings/{meeting.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "PROCESSING"
    assert payload["processing_stage"] == "transcribing"
    assert payload["processing_progress_label"] == "Transcribing audio"
    assert payload["processing_error_message"] is None


def test_notes_api_exposes_safe_processing_error_without_diagnostics(
    db_session: Session,
) -> None:
    user = _create_user(db_session)
    meeting = _create_meeting(db_session, user_id=user.id, status="ERROR")
    mark_failed(meeting, RuntimeError("Provider stack trace token=secret"), stage="transcribing")
    notes = MeetingNotes(
        meeting_id=meeting.id,
        summary="Summary",
        key_points=["Point"],
        action_items=["Action"],
        model_version="test",
    )
    db_session.add(notes)
    db_session.commit()

    app = FastAPI()
    app.include_router(meeting_notes_api.router)

    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[meeting_notes_api._get_db] = override_get_db
    app.dependency_overrides[meeting_notes_api.get_current_user] = lambda: user

    response = TestClient(app).get(f"/v1/meetings/{meeting.id}/notes/ai")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ERROR"
    assert payload["processing_stage"] == "failed"
    assert payload["processing_error_message"] == (
        "Transcription failed. Please try a shorter or clearer recording."
    )
    assert "processing_diagnostics" not in payload
    assert "secret" not in str(payload)


def test_admin_meeting_list_includes_diagnostics_and_timing_metadata(
    db_session: Session,
) -> None:
    admin_user = _create_user(db_session, email="admin@example.com")
    meeting = _create_meeting(db_session, user_id=admin_user.id)
    begin_attempt(meeting)
    mark_failed(meeting, RuntimeError("Provider failed at /private/tmp/audio.mp3"))
    db_session.add(meeting)
    db_session.commit()

    app = FastAPI()
    app.include_router(admin.router)

    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[admin.get_db] = override_get_db
    app.dependency_overrides[admin.require_admin] = lambda: admin_user

    response = TestClient(app).get("/v1/admin/meetings")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["processing_stage"] == "failed"
    assert item["processing_attempts"] == 1
    assert item["processing_error_code"] == "processing_failed"
    assert "processing_failed_at" in item["processing_timings"]
    assert "[path]" in item["processing_diagnostics"]
