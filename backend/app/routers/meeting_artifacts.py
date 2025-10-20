from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Final
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

router = APIRouter(prefix="/v1/meetings", tags=["artifacts"])

STORAGE: Final = Path("storage")
ALLOWED_SUFFIXES: Final = {".pdf", ".png", ".jpg", ".jpeg", ".txt"}


def _meeting_dir(mid: int) -> Path:
    # Prefer .../storage/meetings/{id}, fall back to .../storage/{id}
    candidates = [
        STORAGE / "meetings" / str(mid),
        STORAGE / str(mid),
    ]
    for d in candidates:
        if d.exists():
            return d
    # default to the first layout; do not create for download
    return candidates[0]


def _guess_media_type(p: Path) -> str:
    s = p.suffix.lower()
    overrides = {
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }
    if s in overrides:
        return overrides[s]
    mt, _ = mimetypes.guess_type(p.name)
    return mt or "application/octet-stream"


@router.get("/{meeting_id}/artifacts/slides.zip")
def download_slides_zip(meeting_id: int):
    from pathlib import Path

    # Resolve where artifacts are stored; prefer 'backend/storage/meetings/<id>'
    candidates = [
        Path("backend/storage/meetings") / str(meeting_id),
        Path("backend/storage") / str(meeting_id),
        Path("storage/meetings") / str(meeting_id),
        Path("storage") / str(meeting_id),
    ]
    dir_ = next((d for d in candidates if d.exists()), candidates[0])

    if not dir_.exists():
        raise HTTPException(status_code=404, detail="No artifacts for this meeting")

    files = [
        p for p in sorted(dir_.iterdir()) if p.is_file() and p.suffix.lower() in ALLOWED_SUFFIXES
    ]
    if not files:
        raise HTTPException(status_code=404, detail="No allowed artifacts for this meeting")

    zpath = dir_ / "slides.zip"
    with ZipFile(zpath, "w", ZIP_DEFLATED) as zf:
        for p in files:
            zf.write(p, arcname=p.name)

    return FileResponse(
        str(zpath),
        media_type="application/zip",
        filename=f"meeting_{meeting_id}_slides.zip",
        background=BackgroundTask(lambda: zpath.unlink(missing_ok=True)),
    )
