from __future__ import annotations

from dataclasses import asdict

from backend.app.services.action_consolidation import consolidate_candidate_actions
from backend.app.services.chunk_action_extractor import (
    CandidateAction,
    extract_candidate_actions,
)


def recover_chunk_level_actions(
    transcript: str,
    *,
    max_words_per_chunk: int = 900,
    max_actions: int | None = None,
) -> list[CandidateAction]:
    """Extract and consolidate chunk-level actions from a transcript."""

    candidates = extract_candidate_actions(
        transcript,
        max_words_per_chunk=max_words_per_chunk,
    )
    consolidated = consolidate_candidate_actions(candidates)

    if max_actions is not None:
        return consolidated[:max_actions]

    return consolidated


def recover_chunk_level_action_dicts(
    transcript: str,
    *,
    max_words_per_chunk: int = 900,
    max_actions: int | None = None,
) -> list[dict[str, object]]:
    """Return recovered chunk-level actions as serializable dictionaries."""

    return [
        asdict(action)
        for action in recover_chunk_level_actions(
            transcript,
            max_words_per_chunk=max_words_per_chunk,
            max_actions=max_actions,
        )
    ]
