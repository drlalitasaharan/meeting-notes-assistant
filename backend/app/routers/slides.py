from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from zipfile import ZipFile, ZIP_DEFLATED

from ..db import get_db
from ..deps import require_api_key
from ...packages.shared.models import Meeting

# All slides endpoints live under /v1 and require API key
router = APIRouter(
    prefix="/v1",
    tags=["slides"],
    dependencies=[Depends(require_api_key)],
)

STORAGE = Path("storage")


def _meeting_dir(mid: int) -> Path:
    return STORAGE / str(mid)


@router.post("/meetings/{meeting_id}/slides")
async def upload_slides(
    meeting_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload one or more files for a meeting. Creates storage/{meeting_id}/ if needed.
    """
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    d = _meeting_dir(meeting_id)
    d.mkdir(parents=True, exist_ok=True)

    saved: List[str] = []
    for uf in files:
        # basic filename guard
        name = Path(uf.filename or "").name
        if not name:
            continue
        dest = d / name
        with dest.open("wb") as out:
            while chunk := await uf.read(1024 * 1024):
                out.write(chunk)
        saved.append(name)

    return {"meeting_id": meeting_id, "saved": saved}


@router.get("/meetings/{meeting_id}/slides")
def list_slides(meeting_id: int):
    """
    List uploaded files. Returns 204 if there are no files (acceptable in tests).
    """
    d = _meeting_dir(meeting_id)
    if not d.exists():
        return Response(status_code=204)
    files = sorted([p.name for p in d.iterdir() if p.is_file() and p.name != "slides.zip"])
    if not files:
        return Response(status_code=204)
    return {"files": files}


@router.get("/meetings/{meeting_id}/slides.zip")
def download_slides_zip(meeting_id: int):
    """
    Bundle all uploaded files for a meeting as a zip and return it.
    """
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


@router.get("/meetings/{meeting_id}/slides/{filename}")
def get_slide_file(meeting_id: int, filename: str):
    """
    Download a single uploaded file.
    """
    p = _meeting_dir(meeting_id) / Path(filename).name
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # naive content type switch for txt/pdf
    mt = "text/plain" if p.suffix.lower() == ".txt" else "application/pdf"
    return FileResponse(p, media_type=mt, filename=p.name)

