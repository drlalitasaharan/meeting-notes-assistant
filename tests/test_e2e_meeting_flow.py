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
