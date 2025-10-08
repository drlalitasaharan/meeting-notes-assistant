# backend/app/routers/slides.py
from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from backend.app.core.logger import get_logger
from backend.packages.shared.models import Meeting

from ..deps import get_db, require_api_key

log = get_logger(__name__)

# Make routers version-agnostic; mount /v1 in main.py
router = APIRouter(
    prefix="/meetings",
    tags=["slides"],
    dependencies=[Depends(require_api_key)],
)

STORAGE = Path("storage")


def _meeting_dir(mid: int) -> Path:
    return STORAGE / str(mid)


def _safe_file_path(meeting_id: int, filename: str) -> Path:
    """
    Prevent path traversal by normalizing to basename only.
    """
    name = Path(filename).name
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return _meeting_dir(meeting_id) / name


@router.post("/{meeting_id}/slides", status_code=status.HTTP_201_CREATED)
async def upload_slides(
    meeting_id: int,
    # Accept either "files" (list) or "file" (single/multiple) form field names.
    files: list[UploadFile] | None = File(default=None),
    file: list[UploadFile] | None = File(default=None, alias="file"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Store uploaded files under storage/{meeting_id}/.
    Performs a lightweight meeting existence check.
    Accepts both field names: 'files' and 'file'.
    """
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Choose whichever field was provided
    uploads: list[UploadFile] = (files or []) + (file or [])
    if not uploads:
        raise HTTPException(status_code=400, detail="No files provided")

    d = _meeting_dir(meeting_id)
    d.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    for uf in uploads:
        name = Path(uf.filename).name  # basic filename guard
        if not name:
            raise HTTPException(status_code=400, detail="File has no name")
        dest = d / name
        with dest.open("wb") as out:
            while chunk := await uf.read(1024 * 1024):
                out.write(chunk)
        saved.append(name)
        log.info(
            "Uploaded slide",
            extra={"meeting_id": meeting_id, "filename": name, "content_type": uf.content_type},
        )

    return {"meeting_id": meeting_id, "saved": saved}


@router.get("/{meeting_id}/slides")
def list_slides(meeting_id: int, db: Session = Depends(get_db)) -> list[dict]:
    """
    Return a plain list where each item has a 'filename' key.
    Tests accept either a list[...] or {'items': [...]}; we return a list.
    """
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    d = _meeting_dir(meeting_id)
    if not d.exists():
        return []

    items = [
        {"filename": p.name}
        for p in d.iterdir()
        if p.is_file() and p.name != "slides.zip"
    ]
    return items


@router.get("/{meeting_id}/slides/{filename}")
def get_slide_file(meeting_id: int, filename: str, db: Session = Depends(get_db)) -> FileResponse:
    if not db.get(Meeting, meeting_id):
        raise HTTPException(status_code=404, detail="Meeting not found")

    p = _safe_file_path(meeting_id, filename)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # minimal content-type mapping for tests & previews
    suffix = p.suffix.lower()
    if suffix == ".txt":
        mt = "text/plain"
    elif suffix == ".pdf":
        mt = "application/pdf"
    elif suffix in {".png"}:
        mt = "image/png"
    elif suffix in {".jpg", ".jpeg"}:
        mt = "image/jpeg"
    else:
        mt = "application/octet-stream"

    return FileResponse(p, media_type=mt, filename=p.name)


@router.get("/{meeting_id}/slides.zip")
def download_slides_zip(meeting_id: int, db: Session = Depends(get_db)) -> FileResponse:
    if not db.get(Meeting, meeting_id):
        raise HTTPException(status_code=404, detail="Meeting not found")

    d = _meeting_dir(meeting_id)
    if not d.exists():
        raise HTTPException(status_code=404, detail="No slides uploaded")

    zpath = d / "slides.zip"
    with ZipFile(zpath, "w", ZIP_DEFLATED) as z:
        for p in d.iterdir():
            if p.name == "slides.zip" or not p.is_file():
                continue
            z.write(p, arcname=p.name)

    return FileResponse(
        zpath,
        media_type="application/zip",
        filename=f"meeting-{meeting_id}-slides.zip",
    )


# -----------------------------
# Delete endpoints
# -----------------------------
@router.delete("/{meeting_id}/slides/{filename}", status_code=status.HTTP_204_NO_CONTENT)
def delete_slide_file(meeting_id: int, filename: str, db: Session = Depends(get_db)) -> Response:
    """
    Delete a single slide file under storage/{meeting_id}/.
    Returns 204 on success; 404 if meeting or file not found.
    """
    if not db.get(Meeting, meeting_id):
        raise HTTPException(status_code=404, detail="Meeting not found")

    p = _safe_file_path(meeting_id, filename)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        p.unlink()
        log.info("Deleted slide", extra={"meeting_id": meeting_id, "filename": p.name})
    except Exception as err:
        log.exception(
            "Failed to delete slide",
            extra={"meeting_id": meeting_id, "filename": p.name},
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to delete file",
        ) from err

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{meeting_id}/slides", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_slides(meeting_id: int, db: Session = Depends(get_db)) -> Response:
    """
    OPTIONAL convenience: delete ALL slide files for a meeting (keeps the meeting itself).
    Idempotent: if no directory/files, still returns 204.
    """
    if not db.get(Meeting, meeting_id):
        raise HTTPException(status_code=404, detail="Meeting not found")

    d = _meeting_dir(meeting_id)
    if d.exists():
        for p in d.iterdir():
            if p.is_file() and p.name != "slides.zip":
                try:
                    p.unlink()
                    log.info("Deleted slide", extra={"meeting_id": meeting_id, "filename": p.name})
                except Exception as err:
                    log.exception(
                        "Failed deleting slide",
                        extra={"meeting_id": meeting_id, "filename": p.name},
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to delete {p.name}",
                    ) from err

        # Also remove the zip if it exists (it's derived; safe to drop)
        z = d / "slides.zip"
        if z.exists():
            with suppress(Exception):
                z.unlink()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

