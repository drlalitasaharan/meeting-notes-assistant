from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_PLACEHOLDER_PREFIXES = (
    "tbd",
    "tbd after transcript review",
)

_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
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


@dataclass(frozen=True)
class ExpectedAction:
    owner: str
    action: str
    deadline: str
    source_evidence: str
    notes: str = ""


@dataclass(frozen=True)
class ActualAction:
    action: str
    owner: str = ""
    deadline: str = ""


@dataclass(frozen=True)
class ActionScore:
    expected_count: int
    found_count: int
    recall: float
    owner_accuracy: float | None
    deadline_accuracy: float | None


def load_expected_actions(path: str | Path) -> list[ExpectedAction]:
    """Load must-capture expected actions from a markdown ground-truth file."""

    rows = _load_markdown_table_rows(Path(path))
    expected: list[ExpectedAction] = []

    for row in rows:
        if len(row) < 6:
            continue

        must_capture, owner, action, deadline, source_evidence, notes = row[:6]
        if must_capture.strip().lower() != "yes":
            continue
        if _is_placeholder(action):
            continue

        expected.append(
            ExpectedAction(
                owner=owner.strip(),
                action=action.strip(),
                deadline=deadline.strip(),
                source_evidence=source_evidence.strip(),
                notes=notes.strip(),
            )
        )

    return expected


def load_actual_actions_from_markdown(path: str | Path) -> list[ActualAction]:
    """Load action-like bullet lines from a generated markdown notes file."""

    actual: list[ActualAction] = []
    in_action_section = False

    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if line.startswith("#"):
            in_action_section = "action" in line.lower()
            continue

        if not in_action_section:
            continue

        if line.startswith(("-", "*")):
            cleaned = _clean_bullet(line)
            if cleaned:
                actual.append(ActualAction(action=cleaned))

    return actual


def score_actions(
    expected: list[ExpectedAction],
    actual: list[ActualAction],
) -> ActionScore:
    matched_actual_indexes: set[int] = set()
    owner_total = 0
    owner_correct = 0
    deadline_total = 0
    deadline_correct = 0

    for expected_item in expected:
        match_index = _find_best_match(expected_item, actual, matched_actual_indexes)
        if match_index is None:
            continue

        matched_actual_indexes.add(match_index)
        actual_item = actual[match_index]

        if _is_evaluable_owner(expected_item.owner):
            owner_total += 1
            if _normalise(expected_item.owner) == _normalise(actual_item.owner):
                owner_correct += 1

        if _is_evaluable_deadline(expected_item.deadline):
            deadline_total += 1
            if _normalise(expected_item.deadline) == _normalise(actual_item.deadline):
                deadline_correct += 1

    expected_count = len(expected)
    found_count = len(matched_actual_indexes)
    recall = found_count / expected_count if expected_count else 0.0

    return ActionScore(
        expected_count=expected_count,
        found_count=found_count,
        recall=recall,
        owner_accuracy=(owner_correct / owner_total if owner_total else None),
        deadline_accuracy=(deadline_correct / deadline_total if deadline_total else None),
    )


def _find_best_match(
    expected_item: ExpectedAction,
    actual: list[ActualAction],
    used_indexes: set[int],
) -> int | None:
    best_index: int | None = None
    best_score = 0.0

    for index, actual_item in enumerate(actual):
        if index in used_indexes:
            continue

        similarity = _similarity(expected_item.action, actual_item.action)
        if similarity > best_score:
            best_score = similarity
            best_index = index

    if best_score >= 0.45:
        return best_index

    return None


def _load_markdown_table_rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        if "must_capture" in line:
            continue

        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells:
            rows.append(cells)

    return rows


def _clean_bullet(line: str) -> str:
    cleaned = line.lstrip("-* ").strip()
    if cleaned.startswith("[ ]"):
        cleaned = cleaned[3:].strip()
    if cleaned.startswith("[x]") or cleaned.startswith("[X]"):
        cleaned = cleaned[3:].strip()
    return cleaned


def _is_placeholder(value: str) -> bool:
    normalised = _normalise(value)
    return any(normalised.startswith(prefix) for prefix in _PLACEHOLDER_PREFIXES)


def _is_evaluable_owner(value: str) -> bool:
    normalised = _normalise(value)
    return bool(normalised) and not _is_placeholder(value) and normalised != "unassigned"


def _is_evaluable_deadline(value: str) -> bool:
    normalised = _normalise(value)
    return bool(normalised) and not _is_placeholder(value) and normalised != "no deadline stated"


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

    overlap = len(left_tokens & right_tokens)
    return overlap / min(len(left_tokens), len(right_tokens))
