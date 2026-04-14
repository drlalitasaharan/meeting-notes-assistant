from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .schemas import TranscriptionResult


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str | Path) -> TranscriptionResult:
        raise NotImplementedError
