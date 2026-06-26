from __future__ import annotations

from dataclasses import replace

from app.services.chunk_action_extractor import CandidateAction

_CONFIDENCE_RANK = {
    "low": 1,
    "medium": 2,
    "high": 3,
}

_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "or",
    "the",
    "to",
    "with",
}


def consolidate_candidate_actions(
    candidates: list[CandidateAction],
) -> list[CandidateAction]:
    """Merge duplicate candidate actions without over-merging distinct work."""

    consolidated: list[CandidateAction] = []

    for candidate in sorted(candidates, key=lambda item: item.source_chunk):
        match_index = _find_merge_match(consolidated, candidate)

        if match_index is None:
            consolidated.append(candidate)
            continue

        consolidated[match_index] = _merge_actions(
            consolidated[match_index],
            candidate,
        )

    return sorted(consolidated, key=lambda item: item.source_chunk)


def _find_merge_match(
    consolidated: list[CandidateAction],
    candidate: CandidateAction,
) -> int | None:
    for index, existing in enumerate(consolidated):
        if _should_merge(existing, candidate):
            return index

    return None


def _should_merge(left: CandidateAction, right: CandidateAction) -> bool:
    if _normalise(left.owner) != _normalise(right.owner):
        return False

    if _normalise(left.deadline) != _normalise(right.deadline):
        return False

    return _similarity(left.action, right.action) >= 0.75


def _merge_actions(left: CandidateAction, right: CandidateAction) -> CandidateAction:
    preferred = _more_specific(left, right)
    context = _longer_non_empty(left.reason_context, right.reason_context)

    return replace(
        preferred,
        reason_context=context,
        related_decision=left.related_decision or right.related_decision,
        related_risk=left.related_risk or right.related_risk,
        source_chunk=min(left.source_chunk, right.source_chunk),
        confidence=_best_confidence(left.confidence, right.confidence),
    )


def _more_specific(left: CandidateAction, right: CandidateAction) -> CandidateAction:
    if _specificity_score(right.action) > _specificity_score(left.action):
        return right

    return left


def _specificity_score(value: str) -> int:
    return len(_tokens(value))


def _longer_non_empty(left: str, right: str) -> str:
    if len(right.strip()) > len(left.strip()):
        return right

    return left


def _best_confidence(left: str, right: str) -> str:
    left_rank = _CONFIDENCE_RANK.get(left.lower(), 0)
    right_rank = _CONFIDENCE_RANK.get(right.lower(), 0)

    if right_rank > left_rank:
        return right

    return left


def _normalise(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _tokens(value: str) -> set[str]:
    return {
        token.strip(".,:;!?()[]{}").lower()
        for token in value.split()
        if token.strip(".,:;!?()[]{}").lower()
        and token.strip(".,:;!?()[]{}").lower() not in _STOPWORDS
    }


def _similarity(left: str, right: str) -> float:
    left_norm = _normalise(left)
    right_norm = _normalise(right)

    if not left_norm or not right_norm:
        return 0.0

    if left_norm in right_norm or right_norm in left_norm:
        return 1.0

    left_tokens = _tokens(left_norm)
    right_tokens = _tokens(right_norm)

    if not left_tokens or not right_tokens:
        return 0.0

    return len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))
