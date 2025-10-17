from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Optional

from prometheus_client import Counter, Histogram
from sqlalchemy import asc
from sqlalchemy.orm import Session

from .core.settings import settings
from .db import SessionLocal
from .models import Summary, Transcript

JOB_COUNT = Counter("job_count_by_status", "Jobs by status", ["job", "status"])
JOB_DURATION = Histogram("job_duration_seconds", "Job duration seconds", ["job"])


def ocr_slides(meeting_id: int, slides_dir: Optional[str] = None) -> int:
    import pytesseract
    from PIL import Image

    start = time.time()
    try:
        base = slides_dir or os.path.join("storage", str(meeting_id))
        texts = []
        if not os.path.isdir(base):
            return 0
        for fn in sorted(os.listdir(base)):
            if fn.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
                p = os.path.join(base, fn)
                try:
                    img = Image.open(p)
                    txt = pytesseract.image_to_string(img)
                    if txt.strip():
                        texts.append(f"[{fn}]\n{txt.strip()}")
                except Exception:
                    continue
        if not texts:
            return 0
        db: Session = SessionLocal()
        try:
            t = Transcript(meeting_id=meeting_id, source="ocr", text="\n\n".join(texts))
            db.add(t)
            db.commit()
        finally:
            db.close()
        JOB_COUNT.labels("ocr_slides", "success").inc()
        return len(texts)
    except Exception:
        JOB_COUNT.labels("ocr_slides", "error").inc()
        raise
    finally:
        JOB_DURATION.labels("ocr_slides").observe(time.time() - start)


def summarize_meeting(meeting_id: int, max_chars: int = 8000) -> str:
    start = time.time()
    try:
        db: Session = SessionLocal()
        try:
            texts = (
                db.query(Transcript)
                .filter(Transcript.meeting_id == meeting_id)
                .order_by(asc(Transcript.created_at))
                .all()
            )
            corpus = "\n\n".join(t.text for t in texts)[:max_chars]
        finally:
            db.close()

        if not corpus.strip():
            bullets = "- No transcript or OCR text available."
        else:
            if settings.OPENAI_API_KEY:
                from openai import OpenAI

                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                prompt = (
                    "Summarize as 5–8 crisp bullets. Include key decisions and action items.\n\n"
                    f"Transcript:\n{corpus}"
                )
                resp = client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                )
                content = resp.choices[0].message.content or ""
                bullets = content.strip()
            else:
                lines = [ln.strip() for ln in corpus.splitlines() if ln.strip()]
                bullets = "\n".join(f"- {ln[:160]}" for ln in lines[:8])

        db = SessionLocal()
        try:
            existing = db.query(Summary).filter(Summary.meeting_id == meeting_id).one_or_none()
            if existing:
                setattr(existing, "bullets", bullets)
                existing.created_at = datetime.utcnow()
            else:
                db.add(Summary(meeting_id=meeting_id, bullets=bullets))
            db.commit()
        finally:
            db.close()

        JOB_COUNT.labels("summarize_meeting", "success").inc()
        return "ok"
    except Exception:
        JOB_COUNT.labels("summarize_meeting", "error").inc()
        raise
    finally:
        JOB_DURATION.labels("summarize_meeting").observe(time.time() - start)
