from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TranscriptSection:
    index: int
    title: str
    text: str
    word_count: int


_SECTION_HEADING_RE = re.compile(
    r"(?im)^(?P<speaker>[A-Z][A-Za-z]+):\s*Section\s+(?P<number>\d+)\s*:\s*(?P<title>.+)$"
)


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def split_transcript_sections(transcript_text: str | None) -> list[TranscriptSection]:
    text = str(transcript_text or "").strip()
    if not text:
        return []

    matches = list(_SECTION_HEADING_RE.finditer(text))
    if not matches:
        return [
            TranscriptSection(
                index=1,
                title="Full transcript",
                text=text,
                word_count=_word_count(text),
            )
        ]

    sections: list[TranscriptSection] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        section_text = text[start:end].strip()
        title = match.group("title").strip().rstrip(".")
        sections.append(
            TranscriptSection(
                index=idx + 1,
                title=title,
                text=section_text,
                word_count=_word_count(section_text),
            )
        )

    return sections


def build_long_transcript_section_metadata(transcript_text: str | None) -> dict[str, object]:
    sections = split_transcript_sections(transcript_text)
    if not sections:
        return {
            "section_count": 0,
            "section_titles": [],
            "section_word_counts": [],
            "has_beginning_middle_end_coverage": False,
        }

    return {
        "section_count": len(sections),
        "section_titles": [section.title for section in sections],
        "section_word_counts": [section.word_count for section in sections],
        "has_beginning_middle_end_coverage": len(sections) >= 3,
    }


def select_beginning_middle_end_sections(
    transcript_text: str | None,
) -> list[TranscriptSection]:
    sections = split_transcript_sections(transcript_text)
    if len(sections) <= 3:
        return sections

    selected_positions = [0, (len(sections) - 1) // 2, len(sections) - 1]
    selected: list[TranscriptSection] = []
    seen: set[int] = set()

    for position in selected_positions:
        section = sections[position]
        if section.index in seen:
            continue
        seen.add(section.index)
        selected.append(section)

    return selected


def build_long_transcript_coverage_metadata(transcript_text: str | None) -> dict[str, object]:
    selected_sections = select_beginning_middle_end_sections(transcript_text)

    return {
        "coverage_section_count": len(selected_sections),
        "coverage_section_indices": [section.index for section in selected_sections],
        "coverage_section_titles": [section.title for section in selected_sections],
        "coverage_section_word_counts": [section.word_count for section in selected_sections],
        "has_beginning_middle_end_coverage": len(selected_sections) >= 3,
    }
