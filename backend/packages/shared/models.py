from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, ForeignKey, TIMESTAMP, JSON
import uuid, datetime as dt

class Base(DeclarativeBase):
    pass

def uuid_pk(): 
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    email: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(TIMESTAMP, default=dt.datetime.utcnow)

class Meeting(Base):
    __tablename__ = "meetings"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    title: Mapped[str | None] = mapped_column(String)
    started_at: Mapped[dt.datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    ended_at: Mapped[dt.datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String)  # s3 key for uploaded media
    status: Mapped[str] = mapped_column(String, default="uploaded")
    created_at: Mapped[dt.datetime] = mapped_column(TIMESTAMP, default=dt.datetime.utcnow)

class Transcript(Base):
    __tablename__ = "transcripts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    meeting_id: Mapped[str] = mapped_column(String, ForeignKey("meetings.id"))
    provider: Mapped[str] = mapped_column(String)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    words: Mapped[dict | None] = mapped_column(JSON)  # diarized tokens (optional MVP)
    text: Mapped[str] = mapped_column(Text)

class Slide(Base):
    __tablename__ = "slides"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    meeting_id: Mapped[str] = mapped_column(String, ForeignKey("meetings.id"))
    page: Mapped[int] = mapped_column()
    ocr_text: Mapped[str | None] = mapped_column(Text)
    storage_key: Mapped[str] = mapped_column(String)

class Summary(Base):
    __tablename__ = "summaries"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    meeting_id: Mapped[str] = mapped_column(String, ForeignKey("meetings.id"))
    highlights: Mapped[dict] = mapped_column(JSON)
    decisions: Mapped[dict] = mapped_column(JSON)
    actions: Mapped[dict] = mapped_column(JSON)
    risks: Mapped[dict] = mapped_column(JSON)
    raw_md: Mapped[str] = mapped_column(Text)
