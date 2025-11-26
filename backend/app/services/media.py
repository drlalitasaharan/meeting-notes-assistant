from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app import models


def load_audio_for_meeting(meeting_id: str, video_bytes: bytes) -> bytes:
    """
    TEMPORARY STUB.

    In the final version this will:
      - write the MP4 bytes to a temp file
      - call ffmpeg (or similar) to extract a mono 16kHz WAV
      - return the WAV bytes

    For now we just return the original bytes so the worker pipeline can be wired
    and tests can monkeypatch this function.
    """
    # NOTE: Tests will monkeypatch this to return a known "fake audio" payload.
    return video_bytes


# --- Real MVP: helper to list slide files for a meeting ---
def list_slide_files(db: Session, meeting_id: int) -> list[Path]:
    """
    Return filesystem Paths for all slide artifacts associated with this meeting.

    Assumptions (adjust if your schema differs):
      - If a MeetingArtifact model exists under app.models:
          - meeting_id: foreign key to meetings.id
          - kind (or artifact_type) set to "slide" for slide uploads
          - storage_path: full path on disk / object storage mount

    If no MeetingArtifact model is present yet (e.g. before that migration lands),
    this helper returns an empty list so callers gracefully behave as
    "no slides attached".
    """
    MeetingArtifact = getattr(models, "MeetingArtifact", None)
    if MeetingArtifact is None:
        # Schema does not yet define MeetingArtifact; treat as "no slides".
        return []

    artifacts = (
        db.query(MeetingArtifact)
        .filter(
            MeetingArtifact.meeting_id == meeting_id,
            MeetingArtifact.kind == "slide",
        )
        .all()
    )

    return [Path(getattr(a, "storage_path")) for a in artifacts if getattr(a, "storage_path", None)]
