# app/services/minio_client.py
import os
import io
import os.path
from datetime import timedelta
from typing import List, Dict, Optional

from minio import Minio
from minio.error import S3Error

from app.core.logger import get_logger

log = get_logger(__name__)

MINIO_ENDPOINT    = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
MINIO_ACCESS_KEY  = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY  = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_USE_SSL     = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

# Slides live in this bucket, keys grouped by meeting_id prefix.
SLIDES_BUCKET     = os.getenv("SLIDES_BUCKET", "meeting-slides")
# If your keys are like "meetings/<id>/slides/<file>", set prefix to "meetings/"
SLIDES_KEY_PREFIX = os.getenv("SLIDES_KEY_PREFIX", "")  # e.g. "meetings/"

_minio = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_USE_SSL,
)


# -------------------------------------------------------------------
# Bucket utilities
# -------------------------------------------------------------------
def ensure_bucket() -> None:
    """Idempotently ensure the slides bucket exists."""
    try:
        if not _minio.bucket_exists(SLIDES_BUCKET):
            _minio.make_bucket(SLIDES_BUCKET)
            log.info("Created MinIO bucket", extra={"bucket": SLIDES_BUCKET})
    except S3Error as e:
        log.error("MinIO bucket check/creation failed", extra={"error": str(e)})
        raise


# -------------------------------------------------------------------
# Key helpers
# -------------------------------------------------------------------
def get_meeting_prefix(meeting_id: str) -> str:
    """Prefix for all slide objects for a meeting: '<prefix><meeting_id>/'"""
    return f"{SLIDES_KEY_PREFIX}{meeting_id}/"


def slide_object_key(meeting_id: str, filename: str) -> str:
    """Full object key for a slide under a meeting."""
    return get_meeting_prefix(meeting_id) + filename


# -------------------------------------------------------------------
# Listing & discovery
# -------------------------------------------------------------------
def list_meeting_slides(meeting_id: str) -> List[Dict]:
    """Return slide objects for a meeting: [{key, filename, size, last_modified, etag}]"""
    ensure_bucket()
    prefix = get_meeting_prefix(meeting_id)
    objs = _minio.list_objects(SLIDES_BUCKET, prefix=prefix, recursive=True)
    out = []
    for o in objs:
        # Skip directory placeholders
        if getattr(o, "is_dir", False):
            continue
        out.append({
            "key": o.object_name,
            "filename": o.object_name.split("/")[-1],
            "size": o.size,
            "last_modified": o.last_modified.isoformat() if o.last_modified else None,
            "etag": o.etag,
        })
    return out


def list_all_slides() -> List[Dict]:
    """Return all slides across meetings with inferred meeting_id."""
    ensure_bucket()
    out = []
    for o in _minio.list_objects(SLIDES_BUCKET, recursive=True):
        if getattr(o, "is_dir", False):
            continue
        parts = o.object_name.split("/")
        # meeting_id = first segment after optional prefix
        if SLIDES_KEY_PREFIX and o.object_name.startswith(SLIDES_KEY_PREFIX):
            after = o.object_name[len(SLIDES_KEY_PREFIX):]
            meeting_id = after.split("/")[0]
        else:
            meeting_id = parts[0] if parts else "unknown"
        out.append({
            "meeting_id": meeting_id,
            "key": o.object_name,
            "filename": parts[-1] if parts else o.object_name,
            "size": o.size,
            "last_modified": o.last_modified.isoformat() if o.last_modified else None,
            "etag": o.etag,
        })
    return out


def list_meetings_from_bucket() -> List[Dict]:
    """Infer meetings by top-level prefixes in the bucket."""
    ensure_bucket()
    seen: Dict[str, Dict] = {}
    for o in _minio.list_objects(SLIDES_BUCKET, recursive=True):
        if getattr(o, "is_dir", False):
            continue
        if SLIDES_KEY_PREFIX and o.object_name.startswith(SLIDES_KEY_PREFIX):
            after = o.object_name[len(SLIDES_KEY_PREFIX):]
            meeting_id = after.split("/")[0]
        else:
            meeting_id = o.object_name.split("/")[0]
        info = seen.get(meeting_id, {"meeting_id": meeting_id, "slides_count": 0, "last_slide_at": None})
        info["slides_count"] += 1
        ts = o.last_modified.isoformat() if o.last_modified else None
        if ts and (info["last_slide_at"] is None or ts > info["last_slide_at"]):
            info["last_slide_at"] = ts
        seen[meeting_id] = info
    return sorted(seen.values(), key=lambda x: x["meeting_id"])


# -------------------------------------------------------------------
# Existence checks
# -------------------------------------------------------------------
def slides_exist(meeting_id: str) -> bool:
    """True if the meeting has at least one slide object."""
    ensure_bucket()
    prefix = get_meeting_prefix(meeting_id)
    # list_objects is lazy generator; iterate first element only
    for _ in _minio.list_objects(SLIDES_BUCKET, prefix=prefix, recursive=True):
        return True
    return False


def slide_exists(meeting_id: str, filename: str) -> bool:
    """True if a specific slide exists."""
    ensure_bucket()
    key = slide_object_key(meeting_id, filename)
    try:
        _minio.stat_object(SLIDES_BUCKET, key)
        return True
    except S3Error:
        return False


# -------------------------------------------------------------------
# Upload (put) helpers
# -------------------------------------------------------------------
def put_slide_file(
    meeting_id: str,
    file_path: str,
    filename: Optional[str] = None,
    content_type: str = "application/octet-stream",
) -> str:
    """
    Upload a file from disk into the meeting's prefix.
    Returns the object key.
    """
    ensure_bucket()
    name = filename or os.path.basename(file_path) or "slides.bin"
    key = slide_object_key(meeting_id, name)
    _minio.fput_object(
        SLIDES_BUCKET,
        key,
        file_path,
        content_type=content_type,
    )
    log.info("Uploaded slide file", extra={"bucket": SLIDES_BUCKET, "key": key, "ct": content_type})
    return key


def put_slide_bytes(
    meeting_id: str,
    data: bytes,
    filename: str,
    content_type: str = "application/octet-stream",
) -> str:
    """
    Upload from memory buffer into the meeting's prefix.
    Returns the object key.
    """
    ensure_bucket()
    key = slide_object_key(meeting_id, filename or "slides.bin")
    _minio.put_object(
        SLIDES_BUCKET,
        key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    log.info("Uploaded slide bytes", extra={"bucket": SLIDES_BUCKET, "key": key, "ct": content_type, "len": len(data)})
    return key


# Backwards-compatible alias used by earlier suggestions/APIs
def put_slides(meeting_id: str, file_path: str, content_type: str = "application/octet-stream") -> str:
    """
    Convenience wrapper to upload a single 'slides.bin' from a file path.
    Keeps compatibility with earlier example code.
    """
    return put_slide_file(meeting_id, file_path, filename="slides.bin", content_type=content_type)


# -------------------------------------------------------------------
# Presigned URLs
# -------------------------------------------------------------------
def presigned_slide_get(meeting_id: str, filename: str, expiry_seconds: int = 3600) -> str:
    """Presigned GET URL for a specific slide file."""
    ensure_bucket()
    key = slide_object_key(meeting_id, filename)
    return _minio.presigned_get_object(
        SLIDES_BUCKET,
        key,
        expires=timedelta(seconds=expiry_seconds),
    )


def presigned_first_slide_get(meeting_id: str, expiry_seconds: int = 3600) -> Optional[str]:
    """
    Convenience helper: returns a presigned GET URL for the first slide
    it finds under the meeting's prefix, or None if none exist.
    """
    ensure_bucket()
    prefix = get_meeting_prefix(meeting_id)
    for o in _minio.list_objects(SLIDES_BUCKET, prefix=prefix, recursive=True):
        if getattr(o, "is_dir", False):
            continue
        return _minio.presigned_get_object(
            SLIDES_BUCKET,
            o.object_name,
            expires=timedelta(seconds=expiry_seconds),
        )
    return None

