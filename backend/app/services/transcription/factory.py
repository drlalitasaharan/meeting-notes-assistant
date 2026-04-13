from __future__ import annotations

from .base import Transcriber
from .local_whisper import LocalWhisperTranscriber


def get_transcriber() -> Transcriber:
    return LocalWhisperTranscriber()
