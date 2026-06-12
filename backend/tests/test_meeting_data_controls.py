from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.models.meeting import Meeting
from app.models.meeting_notes import MeetingNotes
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


def _create_meeting_with_notes(db: Session, *, user_id: int) -> Meeting:
    meeting = Meeting(
        title="Meeting to delete",
        user_id=user_id,
        raw_media_path="raw_media/test-recording.m4a",
        status="done",
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    notes = MeetingNotes(
        meeting_id=meeting.id,
        summary="Summary",
        key_points=["Point"],
        action_items=["Action"],
        model_version="test",
    )
    db.add(notes)
    db.commit()
    db.refresh(meeting)
    return meeting


def _client_for(db: Session, user: User) -> TestClient:
    app = FastAPI()
    app.include_router(meetings.router)

    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[meetings.get_db] = override_get_db
    app.dependency_overrides[meetings.get_current_user] = lambda: user

    return TestClient(app)


def test_delete_meeting_removes_owned_meeting_and_generated_notes(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    owner = _create_user(db_session)
    meeting = _create_meeting_with_notes(db_session, user_id=owner.id)
    deleted_paths: list[str | None] = []

    monkeypatch.setattr(
        meetings,
        "delete_raw_media_best_effort",
        lambda raw_media_path: deleted_paths.append(raw_media_path) or True,
    )

    response = _client_for(db_session, owner).delete(f"/v1/meetings/{meeting.id}")

    assert response.status_code == 204
    assert db_session.get(Meeting, meeting.id) is None
    assert db_session.query(MeetingNotes).filter(MeetingNotes.meeting_id == meeting.id).count() == 0
    assert deleted_paths == ["raw_media/test-recording.m4a"]


def test_delete_meeting_does_not_delete_other_users_meeting(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    owner = _create_user(db_session, email="owner@example.com")
    other_user = _create_user(db_session, email="other@example.com")
    meeting = _create_meeting_with_notes(db_session, user_id=owner.id)

    monkeypatch.setattr(
        meetings,
        "delete_raw_media_best_effort",
        lambda raw_media_path: pytest.fail("storage delete should not be called"),
    )

    response = _client_for(db_session, other_user).delete(f"/v1/meetings/{meeting.id}")

    assert response.status_code == 404
    assert db_session.get(Meeting, meeting.id) is not None
    assert db_session.query(MeetingNotes).filter(MeetingNotes.meeting_id == meeting.id).count() == 1
