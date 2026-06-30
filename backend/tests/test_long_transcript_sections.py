from pathlib import Path

from app.services.long_transcript_sections import (
    build_long_transcript_section_metadata,
    split_transcript_sections,
)

FIXTURES = Path("backend/tests/fixtures/meeting_regression")


def test_split_transcript_sections_detects_l01_business_sections():
    transcript = (FIXTURES / "L01_long_business.txt").read_text()

    sections = split_transcript_sections(transcript)

    assert len(sections) >= 10
    assert sections[0].index == 1
    assert "pilot audience" in sections[0].title.lower()
    assert any("recording-duration policy" in section.title.lower() for section in sections)
    assert all(section.word_count > 0 for section in sections)


def test_long_transcript_section_metadata_tracks_beginning_middle_end_coverage():
    transcript = (FIXTURES / "L01_long_business.txt").read_text()

    metadata = build_long_transcript_section_metadata(transcript)

    assert metadata["section_count"] >= 10
    assert metadata["has_beginning_middle_end_coverage"] is True
    assert len(metadata["section_titles"]) == metadata["section_count"]
    assert len(metadata["section_word_counts"]) == metadata["section_count"]


def test_split_transcript_sections_falls_back_to_full_transcript_without_headings():
    sections = split_transcript_sections("Priya: We agreed to send pricing. Alex: I will review.")

    assert len(sections) == 1
    assert sections[0].title == "Full transcript"
    assert sections[0].word_count > 0
