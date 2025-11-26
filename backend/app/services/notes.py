from __future__ import annotations

from typing import Any, Dict, List


def generate_meeting_notes(transcript: Dict[str, Any]) -> Dict[str, Any]:
    """
    TEMPORARY STUB.

    Final contract:

        Input (from transcribe_audio):
        {
          "text": "...",
          "segments": [...],
          "slide_text": "...",  # OPTIONAL: OCR text from slides
        }

        Output:
        {
          "summary": str,
          "key_points": [str],
          "action_items": [str],
          "model_version": str,
        }

    For now we return a simple structure derived from the transcript text (and
    any slide_text) so the rest of the system can be wired and tested with fakes.
    """
    text: str = str(transcript.get("text", "") or "")
    slide_text: str = str(transcript.get("slide_text", "") or "")

    # Combine transcript and slide text for the stub summary.
    if slide_text.strip():
        combined_source = f"{text}\n\n[Slides OCR]\n{slide_text}".strip()
    else:
        combined_source = text

    summary = combined_source if len(combined_source) <= 500 else combined_source[:497] + "..."

    key_points: List[str] = [
        "Placeholder key point – replace with real LLM output.",
    ]
    if slide_text.strip():
        key_points.append("Slide context was included in these notes (OCR stub).")

    action_items: List[str] = [
        "Placeholder action item – replace with real LLM output.",
    ]

    return {
        "summary": summary,
        "key_points": key_points,
        "action_items": action_items,
        "model_version": "stub-notes-v2-slide-aware",
    }
