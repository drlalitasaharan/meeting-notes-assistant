from __future__ import annotations

import re
from typing import Any

LONG_TRANSCRIPT_WORD_THRESHOLD = 7500
VERY_LONG_TRANSCRIPT_WORD_THRESHOLD = 15000


def transcript_word_count(transcript_text: str | None) -> int:
    text = str(transcript_text or "")
    return len(re.findall(r"\b\w+\b", text))


def transcript_line_count(transcript_text: str | None) -> int:
    text = str(transcript_text or "")
    return len([line for line in text.splitlines() if line.strip()])


def build_transcript_observability_metadata(
    transcript_text: str | None,
    *,
    media_duration_seconds: float | int | None = None,
) -> dict[str, Any]:
    text = str(transcript_text or "")
    word_count = transcript_word_count(text)
    line_count = transcript_line_count(text)

    metadata: dict[str, Any] = {
        "transcript_character_count": len(text),
        "transcript_word_count": word_count,
        "transcript_line_count": line_count,
        "transcript_is_long": word_count >= LONG_TRANSCRIPT_WORD_THRESHOLD,
        "transcript_is_very_long": word_count >= VERY_LONG_TRANSCRIPT_WORD_THRESHOLD,
    }

    if media_duration_seconds is not None:
        metadata["media_duration_seconds"] = float(media_duration_seconds)

    return metadata
