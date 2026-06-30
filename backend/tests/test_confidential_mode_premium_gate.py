from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.models.meeting import Meeting
from app.models.user import User
from app.routers import meeting_notes_api


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


def _create_meeting(db: Session, *, user_id: int) -> Meeting:
    meeting = Meeting(
        title="Gate test meeting",
        user_id=user_id,
        status="new",
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def _client_for(db: Session, user: User) -> TestClient:
    app = FastAPI()
    app.include_router(meeting_notes_api.router)

    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[meeting_notes_api._get_db] = override_get_db
    app.dependency_overrides[meeting_notes_api.get_current_user] = lambda: user

    return TestClient(app)


def _patch_successful_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        meeting_notes_api,
        "enforce_free_trial_upload_limit",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        meeting_notes_api,
        "enforce_free_trial_duration_limit",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        meeting_notes_api,
        "probe_media_duration_seconds",
        lambda raw_bytes, suffix: 60.0,
    )
    monkeypatch.setattr(
        meeting_notes_api,
        "_save_raw_media",
        lambda meeting_id, file, raw_bytes: f"s3://test-bucket/raw_media/{meeting_id}.mp3",
    )
    monkeypatch.setattr(
        meeting_notes_api,
        "record_upload_ledger_entry",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        meeting_notes_api,
        "enqueue_process_meeting",
        lambda meeting_id: SimpleNamespace(id=f"job-{meeting_id}"),
    )


def test_non_premium_user_cannot_force_confidential_mode(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    user = _create_user(db_session)
    meeting = _create_meeting(db_session, user_id=user.id)
    client = _client_for(db_session, user)

    monkeypatch.setattr(
        meeting_notes_api,
        "can_use_confidential_mode",
        lambda **kwargs: False,
    )

    response = client.post(
        f"/v1/meetings/{meeting.id}/upload",
        data={"confidential_mode": "true"},
        files={"file": ("test.mp3", b"fake-mp3", "audio/mpeg")},
    )

    assert response.status_code == 403
    assert "Confidential Mode is available" in response.json()["detail"]

    db_session.refresh(meeting)
    assert meeting.confidential_mode is False


def test_non_premium_user_can_upload_without_confidential_mode(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    user = _create_user(db_session)
    meeting = _create_meeting(db_session, user_id=user.id)
    client = _client_for(db_session, user)

    monkeypatch.setattr(
        meeting_notes_api,
        "can_use_confidential_mode",
        lambda **kwargs: False,
    )
    _patch_successful_upload(monkeypatch)

    response = client.post(
        f"/v1/meetings/{meeting.id}/upload",
        data={"confidential_mode": "false"},
        files={"file": ("test.mp3", b"fake-mp3", "audio/mpeg")},
    )

    assert response.status_code == 200

    db_session.refresh(meeting)
    assert meeting.confidential_mode is False
    assert meeting.recording_retention_policy == "standard"
    assert meeting.recording_delete_status == "not_required"


def test_premium_user_can_upload_with_confidential_mode(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    user = _create_user(db_session)
    meeting = _create_meeting(db_session, user_id=user.id)
    client = _client_for(db_session, user)

    monkeypatch.setattr(
        meeting_notes_api,
        "can_use_confidential_mode",
        lambda **kwargs: True,
    )
    _patch_successful_upload(monkeypatch)

    response = client.post(
        f"/v1/meetings/{meeting.id}/upload",
        data={"confidential_mode": "true"},
        files={"file": ("test.mp3", b"fake-mp3", "audio/mpeg")},
    )

    assert response.status_code == 200

    db_session.refresh(meeting)
    assert meeting.confidential_mode is True
    assert meeting.recording_retention_policy == "delete_after_notes"
    assert meeting.recording_delete_status == "pending"
