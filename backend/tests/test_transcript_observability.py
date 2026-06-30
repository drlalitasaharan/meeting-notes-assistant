from app.services.transcript_observability import (
    build_transcript_observability_metadata,
    transcript_line_count,
    transcript_word_count,
)


def test_transcript_word_count_counts_words():
    assert transcript_word_count("Priya will send the approved pricing table.") == 7


def test_transcript_line_count_counts_non_empty_lines():
    text = "Priya: one\n\nAlex: two\n   \nMorgan: three"
    assert transcript_line_count(text) == 3


def test_short_transcript_metadata_is_not_long():
    metadata = build_transcript_observability_metadata(
        "short transcript text",
        media_duration_seconds=120,
    )

    assert metadata["transcript_character_count"] == len("short transcript text")
    assert metadata["transcript_word_count"] == 3
    assert metadata["transcript_line_count"] == 1
    assert metadata["transcript_is_long"] is False
    assert metadata["transcript_is_very_long"] is False
    assert metadata["media_duration_seconds"] == 120.0


def test_long_transcript_metadata_is_long():
    transcript = " ".join(["word"] * 7500)

    metadata = build_transcript_observability_metadata(transcript)

    assert metadata["transcript_word_count"] == 7500
    assert metadata["transcript_is_long"] is True
    assert metadata["transcript_is_very_long"] is False


def test_very_long_transcript_metadata_is_very_long():
    transcript = " ".join(["word"] * 15000)

    metadata = build_transcript_observability_metadata(transcript)

    assert metadata["transcript_word_count"] == 15000
    assert metadata["transcript_is_long"] is True
    assert metadata["transcript_is_very_long"] is True
