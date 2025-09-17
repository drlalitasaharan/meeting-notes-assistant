# app/routers/slides.py
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.core.logger import get_logger
from app.core.db import SessionLocal
from packages.shared.minio_client import (
    upload_fileobj,
    list_keys,
    presign_get,
    SLIDES_BUCKET,
    s3,  # for cleanup on failure
)
from packages.shared.models import Slide as SlideModel

log = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["slides"])


class SlideItem(BaseModel):
    meeting_id: str
    filename: str
    key: str
    size: int | None = None
    last_modified: str | None = None
    url: str | None = None  # presigned GET link


def _slide_key_to_filename(key: str) -> str:
    return key.split("/")[-1] if key else ""


# ---- Attach slides to a meeting (DB is source of truth) ----
@router.post("/meetings/{meeting_id}/attach-slides")
async def attach_slides(meeting_id: str, file: UploadFile):
    """
    Upload a slide file into the slides bucket at slides/{meeting_id}/{filename},
    then INSERT a Slide row in DB. If DB insert fails, delete the uploaded object
    and return 500 to keep DB & S3 consistent.
    """
    key = f"slides/{meeting_id}/{file.filename}"
    content_type = file.content_type or "application/octet-stream"

    # 1) Upload to object storage
    try:
        upload_fileobj(
            file.file,
            key,
            bucket=SLIDES_BUCKET,
            content_type=content_type,  # requires updated minio_client.upload_fileobj
        )
        log.info(
            "Slides uploaded",
            extra={"meeting_id": meeting_id, "key": key, "bucket": SLIDES_BUCKET},
        )
    except Exception:
        log.exception("Slide upload failed", extra={"meeting_id": meeting_id})
        raise HTTPException(
            status_code=500,
            detail={
                "error": "upload_failed",
                "message": "Failed to upload slides.",
                "details": None,
            },
        )

    # 2) Persist a Slide row (MANDATORY)
    try:
        with SessionLocal() as db:
            kwargs = {"meeting_id": meeting_id}
            if hasattr(SlideModel, "id"):
                kwargs["id"] = str(uuid4())

            # Common column names across schemas
            storage_key_field = "storage_key" if hasattr(SlideModel, "storage_key") else ("key" if hasattr(SlideModel, "key") else None)
            if storage_key_field:
                kwargs[storage_key_field] = key

            if hasattr(SlideModel, "page"):
                kwargs["page"] = 0
            if hasattr(SlideModel, "ocr_text"):
                kwargs["ocr_text"] = None
            if hasattr(SlideModel, "filename"):
                kwargs["filename"] = file.filename
            if hasattr(SlideModel, "mime_type"):
                kwargs["mime_type"] = content_type

            # Make sure we have at least meeting_id + storage key linkage
            if not storage_key_field:
                raise ValueError("Slide model lacks a storage key field (storage_key/key)")

            sl = SlideModel(**kwargs)
            db.add(sl)
            db.commit()

    except Exception as e:
        # Cleanup the uploaded object to avoid orphans
        try:
            s3().delete_object(Bucket=SLIDES_BUCKET, Key=key)
        except Exception:
            log.warning("Failed to cleanup slide object after DB error", extra={"key": key})

        log.exception(
            "Slide DB insert failed; upload rolled back",
            extra={"meeting_id": meeting_id, "key": key, "err": str(e)},
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "slide_db_insert_failed",
                "message": "Failed to record slide metadata.",
                "details": None,
            },
        )

    return {"ok": True, "key": key, "bucket": SLIDES_BUCKET}


# ---- List slides for a meeting (DB-first, S3 fallback) ----
@router.get("/meetings/{meeting_id}/slides", response_model=List[SlideItem])
def list_slides_for_meeting(meeting_id: str):
    """
    Prefer DB rows (source of truth) to list slides and attach presigned GET URLs.
    If no DB rows are found (legacy), fall back to listing S3 by prefix.
    Note: Presigned URLs are for GET; using HEAD (-I) may 403 on some servers.
    """
    items: List[SlideItem] = []

    # 1) Try DB
    try:
        with SessionLocal() as db:
            rows = db.query(SlideModel).filter_by(meeting_id=meeting_id).all()
            if rows:
                for row in rows:
                    key = getattr(row, "storage_key", None) or getattr(row, "key", None)
                    filename = getattr(row, "filename", None) or _slide_key_to_filename(key or "")
                    try:
                        url = presign_get(key, expires=900, bucket=SLIDES_BUCKET) if key else None
                    except Exception:
                        url = None
                    items.append(
                        SlideItem(
                            meeting_id=meeting_id,
                            filename=filename or "",
                            key=key or "",
                            url=url,
                        )
                    )
                return items
    except Exception:
        # If DB listing breaks, we’ll log and fall back to S3 listing
        log.warning("DB slide listing failed; falling back to S3", extra={"meeting_id": meeting_id})

    # 2) Fallback: S3 prefix listing
    prefix = f"slides/{meeting_id}/"
    try:
        keys = list_keys(prefix=prefix, bucket=SLIDES_BUCKET) or []
        for k in sorted(keys):
            filename = _slide_key_to_filename(k)
            try:
                url = presign_get(k, expires=900, bucket=SLIDES_BUCKET)
            except Exception:
                url = None
            items.append(
                SlideItem(
                    meeting_id=meeting_id,
                    filename=filename,
                    key=k,
                    url=url,
                )
            )
        return items
    except Exception:
        log.exception("List slides failed", extra={"meeting_id": meeting_id})
        raise HTTPException(
            status_code=500,
            detail={
                "error": "list_slides_failed",
                "message": "Unable to list slides",
                "details": {"meeting_id": meeting_id},
            },
        )


# ---- Return single or first available presigned GET URL (UI convenience) ----
@router.get("/meetings/{meeting_id}/download/slides")
def presign_download(meeting_id: str, filename: Optional[str] = Query(default=None)):
    """
    If filename is provided, presign that exact file; otherwise presign the first file.
    Returns a GET link; use curl without -I, or open in the browser.
    """
    prefix = f"slides/{meeting_id}/"
    try:
        keys = sorted(list_keys(prefix=prefix, bucket=SLIDES_BUCKET) or [])
        if not keys:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "slides_not_found",
                    "message": f"No slides attached for meeting '{meeting_id}'.",
                    "details": None,
                },
            )

        if filename:
            key = f"{prefix}{filename}"
            if key not in keys:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "file_not_found",
                        "message": f"'{filename}' not found for this meeting.",
                        "details": None,
                    },
                )
            url = presign_get(key, expires=900, bucket=SLIDES_BUCKET)
            return {"download_url": url, "filename": filename, "key": key}

        # If only one, return it; otherwise return the first for convenience
        key = keys[0]
        url = presign_get(key, expires=900, bucket=SLIDES_BUCKET)
        return {"download_url": url, "filename": _slide_key_to_filename(key), "key": key}

    except HTTPException:
        raise
    except Exception:
        log.exception("Presign download failed", extra={"meeting_id": meeting_id})
        raise HTTPException(
            status_code=500,
            detail={
                "error": "presign_failed",
                "message": "Could not prepare download link.",
                "details": None,
            },
        )

