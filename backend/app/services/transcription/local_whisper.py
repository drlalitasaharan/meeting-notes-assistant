from __future__ import annotations

import os
from pathlib import Path

from faster_whisper import WhisperModel

from .base import Transcriber
from .schemas import TranscriptionResult, TranscriptionSegment


def _configured_language() -> str | None:
    """Return configured local-whisper language.

    MeetIQ's pilot/local regression recordings are expected to be English.
    faster-whisper language auto-detection can misclassify long English
    meeting audio as a low-confidence non-English language and stall before
    note generation. Default to English while keeping auto-detection available
    through an explicit env override.
    """

    value = (
        os.getenv("MEETIQ_TRANSCRIPTION_LANGUAGE") or os.getenv("TRANSCRIPTION_LANGUAGE") or "en"
    ).strip()

    if not value or value.lower() in {"auto", "detect", "none"}:
        return None

    return value


class LocalWhisperTranscriber(Transcriber):
    def __init__(self) -> None:
        self.model_name = "faster-whisper"
        self.transcription_language = _configured_language()
        self.model = WhisperModel("base", compute_type="int8")

    def transcribe(self, audio_path: str | Path) -> TranscriptionResult:
        transcribe_kwargs: dict[str, str] = {}
        if self.transcription_language:
            transcribe_kwargs["language"] = self.transcription_language

        segments, info = self.model.transcribe(str(audio_path), **transcribe_kwargs)

        segment_list: list[TranscriptionSegment] = []
        text_parts: list[str] = []

        for seg in segments:
            text = seg.text.strip()
            if text:
                text_parts.append(text)

            segment_list.append(
                TranscriptionSegment(
                    start=float(seg.start),
                    end=float(seg.end),
                    text=text,
                )
            )

        return TranscriptionResult(
            text=" ".join(text_parts).strip(),
            language=getattr(info, "language", None) or self.transcription_language,
            duration_seconds=None,
            segments=segment_list,
            model_name=self.model_name,
        )
