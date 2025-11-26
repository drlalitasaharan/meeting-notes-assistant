from __future__ import annotations

from typing import Any, Dict


def test_e2e_meeting_flow_creates_notes(
    client,
    api_headers,
    monkeypatch,
    tmp_path,
) -> None:
    """
    Golden-path test:

      - Create meeting via API
      - Upload fake MP4
      - Run process_meeting() directly
      - Notes are persisted and exposed via /notes/ai and /notes.md
    """
    from app.routers import meeting_notes_api
    from app.services import transcription, notes as notes_svc
    from app.jobs import process_meeting as process_mod

    # --- Fakes / stubs -----------------------------------------------------

    def fake_save_raw_media_stub(meeting_id: str, file, data: bytes) -> str:
        path = tmp_path / f"{meeting_id}.mp4"
        path.write_bytes(data)
        return str(path)

    def fake_transcribe_audio(audio_bytes: bytes) -> Dict[str, Any]:
        return {
            "text": "This is a fake transcript for the E2E flow.",
            "segments": [],
        }

    def fake_generate_meeting_notes(transcript: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "summary": "This is a test summary.",
            "key_points": ["Point A", "Point B"],
            "action_items": ["Do the follow-up thing"],
            "model_version": "test-model",
        }

    # Apply monkeypatches
    monkeypatch.setattr(
        meeting_notes_api,
        "_save_raw_media_stub",
        fake_save_raw_media_stub,
        raising=True,
    )
    monkeypatch.setattr(
        transcription,
        "transcribe_audio",
        fake_transcribe_audio,
        raising=True,
    )
    monkeypatch.setattr(
        notes_svc,
        "generate_meeting_notes",
        fake_generate_meeting_notes,
        raising=True,
    )

    # --- 1) Create meeting via API -----------------------------------------

    r = client.post(
        "/v1/meetings",
        headers=api_headers,
        json={"title": "E2E Meeting", "tags": "e2e"},
    )
    assert r.status_code in (200, 201)
    body = r.json()
    meeting_id = body["id"]

    # --- 2) Upload fake MP4 (just exercise the upload endpoint) ------------

    fake_bytes = b"FAKE_MP4_DATA"
    files = {
        "file": ("test.mp4", fake_bytes, "video/mp4"),
    }
    r2 = client.post(
        f"/v1/meetings/{meeting_id}/upload",
        headers=api_headers,
        files=files,
    )
    assert r2.status_code == 200

    # --- 3) Run the processing job directly --------------------------------

    process_mod.process_meeting(meeting_id)

    # --- 4) Fetch notes via JSON API ---------------------------------------

    r3 = client.get(
        f"/v1/meetings/{meeting_id}/notes/ai",
        headers=api_headers,
    )
    assert r3.status_code == 200
    notes_json = r3.json()

    # For now we only assert the endpoint is live and returns a basic status.
    # The detailed shape of the AI notes payload is covered by lower-level tests.
    assert notes_json.get("status") in ("ok", "DONE")

    # --- 5) Fetch Markdown download ----------------------------------------

    r4 = client.get(
        f"/v1/meetings/{meeting_id}/notes.md",
        headers=api_headers,
    )
    assert r4.status_code == 200
    md = r4.text

    # For now, the E2E contract is that the markdown download route exists and
    # returns a 200 with some body. The exact markdown structure is covered elsewhere.
    assert isinstance(md, str)
    assert md != ""


def test_e2e_meeting_flow_includes_slide_ocr_in_notes(
    client,
    api_headers,
    monkeypatch,
    tmp_path,
) -> None:
    """
    Real MVP behaviour:

      - Create a meeting via API
      - Upload a fake MP4
      - Monkeypatch OCR + notes generation
      - Run process_meeting() directly
      - Assert that:
          * slide OCR text flows into the notes LLM input
          * at least one persisted MeetingNotes.summary includes the slide OCR text.
    """
    from app.routers import meeting_notes_api
    from app.jobs import process_meeting as process_mod
    from app.db import SessionLocal
    from app.models.meeting_notes import MeetingNotes

    SLIDE_TEXT = "SLIDE_OCR_TEXT"

    def fake_save_raw_media_stub(meeting_id: str, file, data: bytes) -> str:
        path = tmp_path / f"{meeting_id}.mp4"
        path.write_bytes(data)
        return str(path)

    def fake_extract_slide_text_for_meeting(db, meeting_id: int) -> str:
        # This is what we want to see reflected in the final notes.
        return SLIDE_TEXT

    def fake_generate_meeting_notes(transcript: Dict[str, Any]) -> Dict[str, Any]:
        # Assert that the job passed OCR text into the notes layer.
        assert transcript.get("slide_text") == SLIDE_TEXT

        text = str(transcript.get("text", ""))
        slide = str(transcript.get("slide_text", ""))

        return {
            "summary": f"Transcript={text} | Slides={slide}",
            "key_points": [f"Slides: {slide}"],
            "action_items": ["Placeholder action item – test only"],
            "model_version": "test-slide-ocr",
        }

    # Apply monkeypatches
    monkeypatch.setattr(
        meeting_notes_api,
        "_save_raw_media_stub",
        fake_save_raw_media_stub,
        raising=True,
    )
    # Patch the names that process_meeting actually calls
    monkeypatch.setattr(
        process_mod,
        "extract_slide_text_for_meeting",
        fake_extract_slide_text_for_meeting,
        raising=True,
    )
    monkeypatch.setattr(
        process_mod,
        "generate_meeting_notes",
        fake_generate_meeting_notes,
        raising=True,
    )

    # 1) Create meeting via API
    r = client.post(
        "/v1/meetings",
        headers=api_headers,
        json={"title": "E2E Meeting with slides", "tags": "e2e,slides"},
    )
    assert r.status_code in (200, 201)
    body = r.json()
    meeting_id = body["id"]

    # 2) Upload fake MP4 (exercise upload endpoint + job enqueue plumbing)
    fake_bytes = b"FAKE_MP4_DATA"
    files = {
        "file": ("test.mp4", fake_bytes, "video/mp4"),
    }
    r2 = client.post(
        f"/v1/meetings/{meeting_id}/upload",
        headers=api_headers,
        files=files,
    )
    assert r2.status_code == 200

    # 3) Run the processing job directly (bypassing RQ worker for tests)
    process_mod.process_meeting(meeting_id)

    # 4) Reload notes from the DB and assert *some* summary has the OCR text
    db = SessionLocal()
    try:
        notes_rows = db.query(MeetingNotes).filter(MeetingNotes.meeting_id == str(meeting_id)).all()
    finally:
        db.close()

    # We expect at least one notes row for this meeting
    assert notes_rows
    # And at least one of them should include the slide OCR text in the summary
    assert any(SLIDE_TEXT in row.summary for row in notes_rows)
