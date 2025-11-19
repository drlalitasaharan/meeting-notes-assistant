from __future__ import annotations


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
