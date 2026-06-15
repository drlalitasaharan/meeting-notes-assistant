from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.deps import get_current_user
from app.models import Base
from app.models.meeting import Meeting
from app.models.upload_ledger import UploadLedger
from app.models.user import User
from app.routers import meetings


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


def _create_user(db: Session, email: str = "trial@example.com") -> User:
    user = User(
        email=email,
        password_hash="not-used-in-test",
        first_name="Trial",
        last_name="User",
        organization_name="Test Org",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_counted_ledger(db: Session, *, user_id: int, meeting_id: str = "existing") -> None:
    ledger = UploadLedger(
        id=f"ledger-{user_id}-{meeting_id}",
        user_id=str(user_id),
        meeting_id=str(meeting_id),
        status="counted",
        counted_at=datetime.now(timezone.utc),
        original_filename="meeting.mp3",
        file_size_bytes=123,
        content_type="audio/mpeg",
        storage_key="s3://bucket/raw_media/meeting.mp3",
    )
    db.add(ledger)
    db.commit()


def _client_for(db: Session, user: User) -> TestClient:
    app = FastAPI()
    app.include_router(meetings.router)

    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[meetings.get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user

    return TestClient(app)


def test_create_meeting_allowed_before_free_trial_used(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("MEETIQ_PILOT_OVERRIDE_EMAILS", raising=False)
    monkeypatch.setenv("MEETIQ_FREE_TRIAL_UPLOAD_LIMIT", "1")

    user = _create_user(db_session)
    client = _client_for(db_session, user)

    response = client.post("/v1/meetings", json={"title": "First meeting"})

    assert response.status_code == 200
    assert db_session.query(Meeting).filter(Meeting.user_id == user.id).count() == 1


def test_create_meeting_blocked_after_lifetime_upload_used_creates_no_row(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("MEETIQ_PILOT_OVERRIDE_EMAILS", raising=False)
    monkeypatch.setenv("MEETIQ_FREE_TRIAL_UPLOAD_LIMIT", "1")

    user = _create_user(db_session)
    _create_counted_ledger(db_session, user_id=user.id)
    client = _client_for(db_session, user)

    response = client.post("/v1/meetings", json={"title": "Second meeting"})

    assert response.status_code == 402
    assert "free-trial upload" in response.json()["detail"]
    assert db_session.query(Meeting).filter(Meeting.user_id == user.id).count() == 0
