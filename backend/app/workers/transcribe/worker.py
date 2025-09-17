# backend/app/workers/transcribe/worker.py
"""
Transcription worker (MVP)

- Uses centralized S3/MinIO client from packages.shared.minio_client
- Structured logging (no prints)
- Safe upsert of Transcript; updates Meeting.status="transcribed"
- CLI via argparse: python worker.py <MEETING_ID> <S3_KEY>
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from uuid import uuid4

from app.core.logger import get_logger
from app.core.db import SessionLocal
from packages.shared.minio_client import s3, RAW_BUCKET
from packages.shared.models import Transcript, Meeting

log = get_logger(__name__)


def _set_if_has(obj, field: str, value):
    if hasattr(obj, field):
        setattr(obj, field, value)


def transcribe_meeting(meeting_id: str, key: str) -> int:
    """
    Download audio from MinIO (RAW bucket), run transcription (mock for MVP),
    and persist a Transcript row. Returns 0 on success, non-zero on failure.
    """
    log.info("Transcription requested", extra={"meeting_id": meeting_id, "key": key, "bucket": RAW_BUCKET})

    # 1) Download to a temporary file
    try:
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            s3().download_file(Bucket=RAW_BUCKET, Key=key, Filename=tmp.name)
            # TODO: Replace this mock with Whisper/AssemblyAI/etc.
            text = "This is a placeholder transcript. Replace with Whisper/AssemblyAI output."
    except Exception:
        log.exception("Download or preprocessing failed", extra={"meeting_id": meeting_id, "key": key})
        return 1

    # 2) Upsert Transcript + update Meeting status
    with SessionLocal() as db:
        try:
            t = db.query(Transcript).filter_by(meeting_id=meeting_id).first()
            if t is None:
                kwargs = {"meeting_id": meeting_id}
                if hasattr(Transcript, "id"):
                    kwargs["id"] = str(uuid4())
                # Fill optional/typical fields if present on your model
                if hasattr(Transcript, "provider"):
                    kwargs["provider"] = "mock"
                if hasattr(Transcript, "language"):
                    kwargs["language"] = "en"
                if hasattr(Transcript, "words"):
                    kwargs["words"] = None
                t = Transcript(**kwargs)
                db.add(t)

            # Always set/update text if the column exists
            _set_if_has(t, "text", text)

            # Update meeting status
            m = db.get(Meeting, meeting_id)
            if m is not None and hasattr(m, "status"):
                m.status = "transcribed"

            db.commit()
            log.info("Transcription saved", extra={"meeting_id": meeting_id})
            return 0
        except Exception:
            db.rollback()
            log.exception("DB write failed", extra={"meeting_id": meeting_id})
            return 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Transcription worker (MVP)")
    parser.add_argument("meeting_id", help="Meeting ID")
    parser.add_argument("s3_key", help="S3/MinIO object key in RAW bucket (e.g., raw/<uuid>.bin)")
    args = parser.parse_args(argv)
    return transcribe_meeting(args.meeting_id, args.s3_key)


if __name__ == "__main__":
    sys.exit(main())

