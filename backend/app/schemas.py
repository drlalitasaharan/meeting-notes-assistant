# app/schemas.py

from pydantic import BaseModel


class MeetingOut(BaseModel):
    id: str
    title: str
    created_at: str
    slides_attached: bool
    transcript_available: bool


class TranscriptOut(BaseModel):
    meeting_id: str
    text: str
    # optional timestamps list of (start, end, text) if you have it
    chunks: list[dict] | None = None


class StartMeetingIn(BaseModel):
    title: str
