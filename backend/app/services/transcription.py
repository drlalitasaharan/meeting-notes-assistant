from __future__ import annotations

from typing import Any, Dict


def transcribe_audio(audio_bytes: bytes) -> Dict[str, Any]:
    """
    TEMPORARY STUB.

    Final contract:

        Returns a dict like:
        {
          "text": "... full transcript ...",
          "segments": [
            {"start": 0.0, "end": 3.2, "speaker": "?", "text": "..."},
            ...
          ],
        }

    For now we just return a small stub transcript so that the rest of the
    pipeline (LLM summarization, persistence, API) can be wired and tested
    with monkeypatches.
    """
    text = "Stub transcript – replace with real Whisper/OpenAI transcription."
    return {"text": text, "segments": []}
