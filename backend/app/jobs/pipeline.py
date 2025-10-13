# backend/app/jobs/pipeline.py
from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

# ---- canonical DB access (replaces old app.db imports) ----
from typing import Dict, Iterable, Iterator, List, Optional

from sqlalchemy.orm import Session

from app.core.db import SessionLocal  # single source of truth


@contextmanager
def session_scope() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# keep old name if the file uses _project_session_scope later
_project_session_scope = session_scope
# -----------------------------------------------------------
# --- Prometheus metrics (safe if not installed) --------------------
try:
    from prometheus_client import Counter, Histogram

    JOB_DUR = Histogram("job_duration_seconds", "RQ job duration", ["job"])
    JOB_COUNT = Counter("job_count_total", "RQ job count", ["job", "status"])
except Exception:

    class _Noop:
        def labels(self, *_, **__):
            return self

        def time(self):
            class _Ctx:
                def __enter__(self):
                    pass

                def __exit__(self, *_):
                    pass

            return _Ctx()

        def inc(self, *_, **__):
            pass

        def observe(self, *_, **__):
            pass

    JOB_DUR = _Noop()
    JOB_COUNT = _Noop()

# --- Optional MinIO support ---------------------------------------
_MINIO_AVAILABLE = False
try:
    from minio import Minio

    _MINIO_AVAILABLE = True
except Exception:
    pass

# --- OCR dependencies (optional; file will still run without them) --
_OCR_AVAILABLE = False
try:
    import pytesseract  # requires Tesseract installed on host/container
    from PIL import Image

    _OCR_AVAILABLE = True
except Exception:
    Image = None
    pytesseract = None

# --- DB session helpers --------------------------------------------
# We try several patterns so this file works with your current project layout.
_SA_AVAILABLE = True
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker
except Exception:
    _SA_AVAILABLE = False
    Session = None  # type: ignore

# Primary: use project's session_scope if present
try:
    # from app.db import session_scope as _project_session_scope  # type: ignore
    def _get_session_scope():
        return _project_session_scope
except Exception:
    # Secondary: use project's SessionLocal if present
    try:
        # from app.db import SessionLocal  # type: ignore
        @contextmanager
        def _session_scope_fallback():
            db = SessionLocal()
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

        def _get_session_scope():
            return _session_scope_fallback
    except Exception:
        # Last resort: create our own engine from env DATABASE_URL
        if not _SA_AVAILABLE:
            raise RuntimeError("SQLAlchemy not available and no project session helpers found.")

        def _engine_from_env():
            url = os.getenv("DATABASE_URL")
            if not url:
                raise RuntimeError("DATABASE_URL not set and no app.db session helpers found.")
            # SQLAlchemy 2.x style engine
            return create_engine(url, pool_pre_ping=True)

        _Engine = _engine_from_env()
        _SessionLocal = sessionmaker(bind=_Engine, autoflush=False, autocommit=False)

        @contextmanager
        def _session_scope_local():
            db = _SessionLocal()
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

        def _get_session_scope():
            return _session_scope_local


session_scope = _get_session_scope()

# --- Models: Transcript & Summary ----------------------------------
# Expecting app.models.notes with Transcript, Summary (created via Alembic migration)
try:
    from app.models.notes import Summary, Transcript  # type: ignore
except Exception as e:
    raise RuntimeError(
        "Missing models app.models.notes.Transcript/Summary. "
        "Create them and run Alembic migration (see earlier steps)."
    ) from e


# ========================= Storage helpers ==========================


def _use_object_storage() -> bool:
    return os.getenv("USE_OBJECT_STORAGE", "false").lower() == "true"


def _minio_client() -> Minio:
    if not _MINIO_AVAILABLE:
        raise RuntimeError(
            "minio package not installed. `pip install minio` or set USE_OBJECT_STORAGE=false."
        )
    return Minio(
        os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minio"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minio123"),
        secure=os.getenv("MINIO_USE_SSL", "false").lower() == "true",
    )


def _list_local_slide_paths(meeting_id: int) -> List[Path]:
    d = Path("storage") / str(meeting_id)
    if not d.is_dir():
        return []
    return [p for p in d.iterdir() if p.is_file()]


def _download_minio_to_temp(meeting_id: int, tmpdir: Path) -> List[Path]:
    """Download objects under {meeting_id}/ prefix to tmpdir. Returns file paths."""
    bucket = os.getenv("SLIDES_BUCKET", "meeting-slides")
    mc = _minio_client()
    found: List[Path] = []
    # Ensure bucket exists (idempotent)
    try:
        if not mc.bucket_exists(bucket):
            mc.make_bucket(bucket)
    except Exception:
        # if perms prevent creation, we continue; list may still work
        pass

    prefix = f"{meeting_id}/"
    for obj in mc.list_objects(bucket, prefix=prefix, recursive=True):
        # skip folder markers
        name = obj.object_name
        if name.endswith("/"):
            continue
        data = mc.get_object(bucket, name)
        try:
            content = data.read()  # type: ignore[attr-defined]
        finally:
            try:
                data.close()  # type: ignore[attr-defined]
            except Exception:
                pass
        fname = name.split("/", 1)[-1] if "/" in name else name
        dst = tmpdir / fname
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "wb") as f:
            f.write(content)
        found.append(dst)
    return found


def _gather_slide_files(meeting_id: int) -> List[Path]:
    """Return local paths to slide files, downloading from MinIO when enabled."""
    if _use_object_storage():
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            files = _download_minio_to_temp(meeting_id, td_path)
            # NOTE: We cannot return paths that live inside a TemporaryDirectory
            # after the context exits; so we copy to a persistent temp.
            persist = Path(tempfile.mkdtemp(prefix=f"slides-{meeting_id}-"))
            keep: List[Path] = []
            for p in files:
                dst = persist / p.name
                dst.write_bytes(p.read_bytes())
                keep.append(dst)
            return keep
    else:
        return _list_local_slide_paths(meeting_id)


# ============================= OCR =================================

_IMG_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def _ocr_images(paths: Iterable[Path]) -> str:
    """OCR only image files. PDFs can be added later via pdf2image."""
    if not _OCR_AVAILABLE:
        # OCR libs not present, return empty string gracefully
        return ""
    out: list[str] = []
    for p in paths:
        if p.suffix.lower() not in _IMG_EXTS:
            continue
        try:
            with Image.open(p) as im:  # type: ignore
                txt = pytesseract.image_to_string(im)  # type: ignore
                if txt and txt.strip():
                    out.append(txt.strip())
        except Exception:
            # Keep robust—skip unreadable files
            continue
    return "\n".join(out).strip()


# =========================== Summarize ==============================


def _summarize_text(text: str) -> str:
    """
    Fallback summarizer. If OPENAI_API_KEY is set and `openai` is installed,
    you can switch to a real LLM summary by uncommenting the block below.
    """
    if not text.strip():
        return ""
    # --- Real LLM example (optional) ---
    """
    import os
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    prompt = (
        "Summarize the meeting transcript into crisp bullet points focusing on "
        "decisions, owners, and deadlines. Keep it under 10 bullets."
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content":prompt},
            {"role":"user","content":text[:12000]}
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()
    """
    # Simple local fallback: first few lines as bullets
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    head = lines[:10]
    return "• " + "\n• ".join(head) if head else ""


# =========================== Main job ===============================


def process_meeting(meeting_id: int) -> Dict:
    """
    RQ job entry point: gather slides (local or MinIO), OCR images to Transcript,
    generate Summary, and persist both to DB.

    Returns a small JSON-serializable dict for job result.
    """
    with JOB_DUR.labels("process_meeting").time():
        try:
            # 1) Collect slide files
            slide_files = _gather_slide_files(meeting_id)

            # 2) OCR images -> transcript text
            transcript_text = _ocr_images(slide_files)

            # 3) Persist Transcript (if any)
            saved_transcript_id: Optional[int] = None
            saved_summary_id: Optional[int] = None

            if _SA_AVAILABLE:
                with session_scope() as db:  # type: ignore
                    if transcript_text.strip():
                        t = Transcript(meeting_id=meeting_id, text=transcript_text)  # type: ignore
                        db.add(t)
                        db.flush()
                        saved_transcript_id = getattr(t, "id", None)

                    # 4) Summarize latest transcript (or use freshly OCR'd text)
                    basis_text = transcript_text
                    if not basis_text and saved_transcript_id is None:
                        # No new OCR—try latest existing transcript for the meeting
                        try:
                            from sqlalchemy import desc  # type: ignore

                            t_latest = (
                                db.query(Transcript)  # type: ignore
                                .filter(Transcript.meeting_id == meeting_id)  # type: ignore
                                .order_by(desc(Transcript.created_at))  # type: ignore
                                .first()
                            )
                            if t_latest and t_latest.text:
                                basis_text = t_latest.text
                        except Exception:
                            pass

                    summary_text = _summarize_text(basis_text) if basis_text else ""
                    if summary_text.strip():
                        s = Summary(meeting_id=meeting_id, text=summary_text)  # type: ignore
                        db.add(s)
                        db.flush()
                        saved_summary_id = getattr(s, "id", None)
            else:
                # If SQLAlchemy is unavailable, we still do the CPU work and return the content.
                saved_transcript_id = None
                saved_summary_id = None

            JOB_COUNT.labels("process_meeting", "success").inc()
            return {
                "ok": True,
                "meeting_id": meeting_id,
                "slides_found": len(slide_files),
                "transcript_chars": len(transcript_text),
                "transcript_id": saved_transcript_id,
                "summary_id": saved_summary_id,
                "used_object_storage": _use_object_storage(),
            }
        except Exception:
            JOB_COUNT.labels("process_meeting", "error").inc()
            # Re-raise so RQ marks job as failed and stores traceback
            raise
