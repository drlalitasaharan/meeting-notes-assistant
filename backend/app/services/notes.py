from __future__ import annotations

from typing import Any, Dict, List


def generate_meeting_notes(transcript: Dict[str, Any]) -> Dict[str, Any]:
    """
    TEMPORARY STUB.

    Final contract:

        Input (from transcribe_audio):
        {
          "text": "...",
          "segments": [...]
        }

        Output:
        {
          "summary": str,
          "key_points": [str],
          "action_items": [str],
          "model_version": str,
        }

    For now we return a simple structure derived from the transcript text so the
    rest of the system can be wired and tested with fakes.
    """
    text: str = transcript.get("text", "") or ""
    summary = text if len(text) <= 500 else text[:497] + "..."

    key_points: List[str] = [
        "Placeholder key point – replace with real LLM output.",
    ]
    action_items: List[str] = [
        "Placeholder action item – replace with real LLM output.",
    ]

    return {
        "summary": summary,
        "key_points": key_points,
        "action_items": action_items,
        "model_version": "stub-notes-v1",
    }
