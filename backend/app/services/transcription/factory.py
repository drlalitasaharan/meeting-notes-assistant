from __future__ import annotations

import os

from .base import Transcriber


def get_transcriber() -> Transcriber:
    provider = os.getenv("TRANSCRIPTION_PROVIDER", "").strip().lower()

    if not provider:
        provider = "openai" if os.getenv("OPENAI_API_KEY") else "local_whisper"

    if provider in {"openai", "openai_whisper", "whisper_api"}:
        from .openai_whisper import OpenAIWhisperTranscriber

        return OpenAIWhisperTranscriber()

    if provider in {"local", "local_whisper", "faster_whisper"}:
        from .local_whisper import LocalWhisperTranscriber

        return LocalWhisperTranscriber()

    raise RuntimeError(f"Unsupported TRANSCRIPTION_PROVIDER={provider!r}")
