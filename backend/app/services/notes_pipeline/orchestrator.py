from __future__ import annotations

from app.schemas.meeting_notes import MeetingNotesCanonical
from app.services.notes_pipeline.chunking import chunk_text
from app.services.notes_pipeline.compose import compose_summary, to_markdown
from app.services.notes_pipeline.extract_slots import extract_from_chunks
from app.services.notes_pipeline.merge_slots import merge_canonical
from app.services.notes_pipeline.normalize import normalize_transcript_text
from app.services.notes_pipeline.validate import validate_canonical


def build_canonical_notes(meeting_id: int, transcript_text: str) -> MeetingNotesCanonical:
    normalized = normalize_transcript_text(transcript_text)
    chunks = chunk_text(normalized)

    notes = extract_from_chunks(meeting_id=meeting_id, chunks=chunks)
    notes = merge_canonical(notes)
    notes = validate_canonical(notes)
    notes.summary = compose_summary(notes)

    notes.metadata.transcript_quality = 0.90 if normalized else 0.0
    return notes


def build_markdown(notes: MeetingNotesCanonical) -> str:
    return to_markdown(notes)
