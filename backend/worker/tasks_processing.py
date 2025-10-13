import os, glob
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Table, Column, Integer, Text, DateTime, String, MetaData, create_engine
from sqlalchemy.engine import Engine

from app.summarizers import summarize_simple

# Optional OCR imports
try:
    from PIL import Image
    import pytesseract
except Exception:
    Image = None  # type: ignore
    pytesseract = None  # type: ignore

DB_URL = os.getenv("DATABASE_URL", "sqlite:////app/backend/dev.db")
engine: Engine = create_engine(DB_URL, future=True)

md = MetaData()
transcripts = Table(
    "transcripts", md,
    Column("id", Integer, primary_key=True),
    Column("meeting_id", Integer, nullable=False),
    Column("text", Text, nullable=False),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)
summaries = Table(
    "summaries", md,
    Column("id", Integer, primary_key=True),
    Column("meeting_id", Integer, nullable=False),
    Column("model", String(60), nullable=False, default="simple"),
    Column("text", Text, nullable=False),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)

def _find_storage_dir(meeting_id: int) -> str:
    candidates = [
        f"/app/backend/storage/{meeting_id}",
        f"/app/storage/{meeting_id}",
        f"/storage/{meeting_id}",
        os.path.join(os.getcwd(), "backend", "storage", str(meeting_id)),
        os.path.join(os.getcwd(), "storage", str(meeting_id)),
    ]
    for p in candidates:
        if os.path.isdir(p):
            return p
    p = f"/app/backend/storage/{meeting_id}"
    os.makedirs(p, exist_ok=True)
    return p

def _gather_text(storage_dir: str) -> str:
    chunks = []
    for ext in ("*.txt", "*.md"):
        for path in glob.glob(os.path.join(storage_dir, ext)):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    chunks.append(fh.read())
            except Exception:
                pass

    if not chunks and Image and pytesseract:
        for ext in ("*.png", "*.jpg", "*.jpeg"):
            for path in glob.glob(os.path.join(storage_dir, ext)):
                try:
                    txt = pytesseract.image_to_string(Image.open(path))
                    if txt.strip():
                        chunks.append(txt)
                except Exception:
                    continue

    if not chunks:
        return "No readable content found."
    return "\n\n".join(chunks)

def process_meeting(meeting_id: int) -> dict:
    storage_dir = _find_storage_dir(int(meeting_id))
    text = _gather_text(storage_dir)

    with engine.begin() as conn:
        # Insert transcript
        r = conn.execute(transcripts.insert().values(
            meeting_id=int(meeting_id),
            text=text
        ))
        transcript_id = r.inserted_primary_key[0]

        # Create summary (simple)
        summ_text = summarize_simple(text, sentences=3)
        r2 = conn.execute(summaries.insert().values(
            meeting_id=int(meeting_id),
            model="simple",
            text=summ_text
        ))
        summary_id = r2.inserted_primary_key[0]

    return {
        "meeting_id": int(meeting_id),
        "transcript_id": transcript_id,
        "summary_id": summary_id,
    }
