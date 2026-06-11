from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.models.meeting import Meeting
from app.models.user import User
from app.services.usage_limits import (
    count_uploaded_meeting_slots,
    enforce_free_trial_upload_limit,
    upload_limit_for_user,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_user(db_session, email: str = "trial@example.com") -> User:
    user = User(
        email=email,
        password_hash="not-used-in-test",
        first_name="Trial",
        last_name="User",
        organization_name="Test Org",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_meeting(
    db_session,
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
    db_session.add(meeting)
    db_session.commit()
    db_session.refresh(meeting)
    return meeting


def test_free_trial_allows_first_uploaded_meeting_slot(db_session, monkeypatch):
    monkeypatch.delenv("MEETIQ_PILOT_OVERRIDE_EMAILS", raising=False)
    monkeypatch.setenv("MEETIQ_FREE_TRIAL_UPLOAD_LIMIT", "1")

    user = _create_user(db_session)
    meeting = _create_meeting(db_session, user_id=user.id, title="First meeting")

    enforce_free_trial_upload_limit(
        db=db_session,
        current_user=user,
        meeting=meeting,
    )

    assert upload_limit_for_user(user) == 1
    assert count_uploaded_meeting_slots(db_session, user_id=user.id) == 0


def test_free_trial_blocks_second_uploaded_meeting_slot(db_session, monkeypatch):
    monkeypatch.delenv("MEETIQ_PILOT_OVERRIDE_EMAILS", raising=False)
    monkeypatch.setenv("MEETIQ_FREE_TRIAL_UPLOAD_LIMIT", "1")

    user = _create_user(db_session)

    _create_meeting(
        db_session,
        user_id=user.id,
        title="Already uploaded",
        raw_media_path="s3://bucket/raw_media/meeting_1.m4a",
    )
    second_meeting = _create_meeting(
        db_session,
        user_id=user.id,
        title="Second meeting",
    )

    with pytest.raises(HTTPException) as exc:
        enforce_free_trial_upload_limit(
            db=db_session,
            current_user=user,
            meeting=second_meeting,
        )

    assert exc.value.status_code == 402
    assert "Free trial limit reached" in exc.value.detail


def test_pilot_override_allows_three_uploaded_meeting_slots(db_session, monkeypatch):
    monkeypatch.setenv("MEETIQ_PILOT_OVERRIDE_EMAILS", "pilot@example.com")
    monkeypatch.setenv("MEETIQ_PILOT_UPLOAD_LIMIT", "3")

    user = _create_user(db_session, email="pilot@example.com")

    _create_meeting(
        db_session,
        user_id=user.id,
        title="Uploaded 1",
        raw_media_path="s3://bucket/raw_media/meeting_1.m4a",
    )
    _create_meeting(
        db_session,
        user_id=user.id,
        title="Uploaded 2",
        raw_media_path="s3://bucket/raw_media/meeting_2.m4a",
    )
    third_meeting = _create_meeting(
        db_session,
        user_id=user.id,
        title="Third meeting",
    )

    enforce_free_trial_upload_limit(
        db=db_session,
        current_user=user,
        meeting=third_meeting,
    )

    assert upload_limit_for_user(user) == 3
