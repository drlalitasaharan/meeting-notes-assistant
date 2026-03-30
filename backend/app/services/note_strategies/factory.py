from __future__ import annotations

from app.core.settings import settings

from .llm_summary import LLMSummaryStrategy
from .local_summary import LocalSummaryStrategy


def get_notes_strategy():
    strategy = getattr(settings, "NOTES_STRATEGY", "local_summary")

    if strategy == "llm":
        return LLMSummaryStrategy()

    return LocalSummaryStrategy()
