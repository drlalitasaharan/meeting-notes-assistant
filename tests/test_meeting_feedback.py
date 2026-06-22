from __future__ import annotations

import uuid

from app.core.db import SessionLocal
from app.models.meeting_feedback import MeetingFeedback


def _signup(client, email: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "Feedback",
            "last_name": "User",
            "organization_name": "MeetIQ Tests",
        },
    )
    assert response.status_code in (200, 201), response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_meeting(client, headers: dict[str, str], title: str = "Feedback sync") -> int:
    response = client.post("/v1/meetings", json={"title": title}, headers=headers)
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


def _feedback_payload(meeting_id: int, **overrides):
    payload = {
        "meeting_id": meeting_id,
        "usefulness": "yes",
        "most_useful": "summary",
        "improvement_text": "More detail on decisions would help.",
        "would_use_again": "yes",
        "meeting_type": "client",
    }
    payload.update(overrides)
    return payload


def test_authenticated_user_can_submit_feedback_for_own_meeting(client, api_headers):
    meeting_id = _create_meeting(client, api_headers)

    response = client.post(
        "/v1/feedback/meeting",
        json=_feedback_payload(meeting_id),
        headers=api_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["meeting_id"] == meeting_id
    assert body["usefulness"] == "yes"
    assert body["most_useful"] == "summary"
    assert body["would_use_again"] == "yes"
    assert body["meeting_type"] == "client"
    assert body["improvement_text"] == "More detail on decisions would help."


def test_submitting_feedback_twice_updates_existing_row(client, api_headers):
    meeting_id = _create_meeting(client, api_headers)

    first = client.post(
        "/v1/feedback/meeting",
        json=_feedback_payload(meeting_id),
        headers=api_headers,
    )
    assert first.status_code == 200, first.text

    second = client.post(
        "/v1/feedback/meeting",
        json=_feedback_payload(
            meeting_id,
            usefulness="somewhat",
            most_useful="action_items",
            improvement_text="Add clearer owners.",
            would_use_again="maybe",
            meeting_type="internal",
        ),
        headers=api_headers,
    )

    assert second.status_code == 200, second.text
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["usefulness"] == "somewhat"
    assert second.json()["improvement_text"] == "Add clearer owners."

    with SessionLocal() as db:
        count = db.query(MeetingFeedback).filter(MeetingFeedback.meeting_id == meeting_id).count()
    assert count == 1


def test_user_cannot_submit_feedback_for_another_users_meeting(client):
    owner_headers = _signup(client, f"owner-{uuid.uuid4().hex}@example.com")
    other_headers = _signup(client, f"other-{uuid.uuid4().hex}@example.com")
    meeting_id = _create_meeting(client, owner_headers)

    response = client.post(
        "/v1/feedback/meeting",
        json=_feedback_payload(meeting_id),
        headers=other_headers,
    )

    assert response.status_code == 404


def test_invalid_feedback_enum_value_returns_validation_error(client, api_headers):
    meeting_id = _create_meeting(client, api_headers)

    response = client.post(
        "/v1/feedback/meeting",
        json=_feedback_payload(meeting_id, usefulness="definitely"),
        headers=api_headers,
    )

    assert response.status_code == 422


def test_improvement_text_can_be_blank_or_omitted(client, api_headers):
    meeting_id = _create_meeting(client, api_headers)

    blank_response = client.post(
        "/v1/feedback/meeting",
        json=_feedback_payload(meeting_id, improvement_text="   "),
        headers=api_headers,
    )
    assert blank_response.status_code == 200, blank_response.text
    assert blank_response.json()["improvement_text"] is None

    omitted_payload = _feedback_payload(meeting_id, usefulness="no", would_use_again="no")
    omitted_payload.pop("improvement_text")
    omitted_response = client.post(
        "/v1/feedback/meeting",
        json=omitted_payload,
        headers=api_headers,
    )

    assert omitted_response.status_code == 200, omitted_response.text
    assert omitted_response.json()["improvement_text"] is None
