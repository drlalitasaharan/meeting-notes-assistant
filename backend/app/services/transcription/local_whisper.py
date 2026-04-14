from __future__ import annotations

from pathlib import Path

from faster_whisper import WhisperModel

from .base import Transcriber
from .schemas import TranscriptionResult, TranscriptionSegment


class LocalWhisperTranscriber(Transcriber):
    def __init__(self) -> None:
        self.model_name = "faster-whisper"
        self.model = WhisperModel("base", compute_type="int8")

    def transcribe(self, audio_path: str | Path) -> TranscriptionResult:
        segments, info = self.model.transcribe(str(audio_path))

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
            language=getattr(info, "language", None),
            duration_seconds=None,
            segments=segment_list,
            model_name=self.model_name,
        )
