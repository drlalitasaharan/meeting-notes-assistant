from __future__ import annotations

from .base import NotesResult, NotesStrategy
from .local_summary import LocalSummaryStrategy


class LLMSummaryStrategy(NotesStrategy):
    def generate(self, transcript_text: str, slide_text: str = "") -> NotesResult:
        try:
            raise NotImplementedError("LLM path not wired yet")
        except Exception:
            result = LocalSummaryStrategy().generate(transcript_text, slide_text)
            result.model_version = "local-summary-v1-fallback"
            return result
