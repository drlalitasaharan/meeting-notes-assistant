from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from openai import OpenAI

from .base import Transcriber
from .schemas import TranscriptionResult, TranscriptionSegment


def _to_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return dict(value)


class OpenAIWhisperTranscriber(Transcriber):
    def __init__(self) -> None:
        self.model_name = os.getenv("OPENAI_TRANSCRIPTION_MODEL", "whisper-1")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def transcribe(self, audio_path: str | Path) -> TranscriptionResult:
        with Path(audio_path).open("rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=self.model_name,
                file=audio_file,
                response_format="verbose_json",
            )

        data = _to_dict(response)

        segments: list[TranscriptionSegment] = []
        for seg in data.get("segments") or []:
            seg_dict = _to_dict(seg)
            text = str(seg_dict.get("text") or "").strip()
            if not text:
                continue

            segments.append(
                TranscriptionSegment(
                    start=float(seg_dict.get("start") or 0.0),
                    end=float(seg_dict.get("end") or 0.0),
                    text=text,
                )
            )

        return TranscriptionResult(
            text=str(data.get("text") or "").strip(),
            language=data.get("language"),
            duration_seconds=data.get("duration"),
            segments=segments,
            model_name=self.model_name,
        )
