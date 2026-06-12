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
from app.models.user import User
from app.routers import usage


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


def _create_meeting(
    db: Session,
    *,
    user_id: int,
    title: str,
    raw_media_path: str | None = None,
) -> Meeting:
    meeting = Meeting(
        title=title,
        user_id=user_id,
        raw_media_path=raw_media_path,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def _client_for(db: Session, user: User) -> TestClient:
    app = FastAPI()
    app.include_router(usage.router)

    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[usage._get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user

    return TestClient(app)


def test_usage_dashboard_returns_free_trial_usage(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("MEETIQ_PILOT_OVERRIDE_EMAILS", raising=False)
    monkeypatch.setenv("MEETIQ_FREE_TRIAL_UPLOAD_LIMIT", "1")
    monkeypatch.setenv("MEETIQ_FREE_TRIAL_MAX_DURATION_SECONDS", "1800")

    user = _create_user(db_session)
    _create_meeting(
        db_session,
        user_id=user.id,
        title="Uploaded meeting",
        raw_media_path="s3://bucket/raw_media/meeting_1.m4a",
    )

    response = _client_for(db_session, user).get("/v1/usage/me")

    assert response.status_code == 200
    payload = response.json()
    assert payload["plan"] == "free_trial"
    assert payload["is_pilot_override"] is False
    assert payload["meetings_used"] == 1
    assert payload["meeting_upload_limit"] == 1
    assert payload["remaining_uploads"] == 0
    assert payload["max_duration_seconds"] == 1800
    assert payload["max_duration_minutes"] == 30


def test_usage_dashboard_returns_pilot_usage(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("MEETIQ_PILOT_OVERRIDE_EMAILS", "pilot@example.com")
    monkeypatch.setenv("MEETIQ_PILOT_UPLOAD_LIMIT", "3")
    monkeypatch.setenv("MEETIQ_PILOT_MAX_DURATION_SECONDS", "3600")

    user = _create_user(db_session, email="pilot@example.com")
    _create_meeting(
        db_session,
        user_id=user.id,
        title="Uploaded meeting 1",
        raw_media_path="s3://bucket/raw_media/meeting_1.m4a",
    )
    _create_meeting(
        db_session,
        user_id=user.id,
        title="Uploaded meeting 2",
        raw_media_path="s3://bucket/raw_media/meeting_2.m4a",
    )

    response = _client_for(db_session, user).get("/v1/usage/me")

    assert response.status_code == 200
    payload = response.json()
    assert payload["plan"] == "pilot"
    assert payload["is_pilot_override"] is True
    assert payload["meetings_used"] == 2
    assert payload["meeting_upload_limit"] == 3
    assert payload["remaining_uploads"] == 1
    assert payload["max_duration_seconds"] == 3600
    assert payload["max_duration_minutes"] == 60
