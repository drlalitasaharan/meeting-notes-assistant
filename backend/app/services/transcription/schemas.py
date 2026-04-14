from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class TranscriptionSegment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    text: str
    language: str | None
    duration_seconds: float | None
    segments: list[TranscriptionSegment]
    model_name: str

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "language": self.language,
            "duration_seconds": self.duration_seconds,
            "segments": [asdict(s) for s in self.segments],
            "model_name": self.model_name,
        }
