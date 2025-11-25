from __future__ import annotations

from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from . import media


def extract_slide_text_for_meeting(db: Session, meeting_id: int) -> str:
    """
    Return OCR text for all slides attached to this meeting.

    Real OCR can be plugged in later. For now, we:
    - ask media.list_slide_files(...) for slide paths
    - build a deterministic stub so tests can assert on behaviour.

    Note: media.list_slide_files is added in a follow-up branch; we ignore
    the type error here and wire it up properly later.
    """
    slide_files: List[Path] = media.list_slide_files(  # type: ignore[attr-defined]
        db=db,
        meeting_id=meeting_id,
    )

    if not slide_files:
        return ""

    # Stub: just mention each slide filename.
    # Tests can monkeypatch this function to return "SLIDE_OCR_TEXT".
    parts = [f"[OCR STUB for slide: {path.name}]" for path in slide_files]
    return "\n\n".join(parts)
