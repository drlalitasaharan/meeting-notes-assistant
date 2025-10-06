from __future__ import annotations

import argparse
import sys

from backend.packages.shared.models import Meeting, Transcript

from app.core.db import SessionLocal
from app.core.logger import get_logger

log = get_logger(__name__)


def _download_and_preprocess(key: str) -> bytes:
    """
    Replace this stub with your real download and preprocessing.
    For now we just return empty bytes to demonstrate flow.
    """
    return b""


def transcribe_meeting(meeting_id: int) -> int:
    with SessionLocal() as db:
        m = db.get(Meeting, meeting_id)
        if not m:
            log.warning("Meeting not found", extra={"meeting_id": meeting_id})
            return 1

        key = f"raw/{meeting_id}/audio.wav"
        try:
            _download_and_preprocess(key)
        except Exception:
            log.exception(
                "Download or preprocessing failed",
                extra={"meeting_id": meeting_id, "key": key},
            )
            return 1

        # Mock transcription content
        text = "This is a mock transcript."

        t = Transcript(meeting_id=meeting_id, text=text)
        db.add(t)
        db.commit()
        log.info("Transcription stored", extra={"meeting_id": meeting_id, "transcript_id": t.id})
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--meeting-id", type=int, required=True)
    args = parser.parse_args(argv)
    return transcribe_meeting(args.meeting_id)


if __name__ == "__main__":
    sys.exit(main())

