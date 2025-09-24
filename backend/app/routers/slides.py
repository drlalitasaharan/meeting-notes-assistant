from __future__ import annotations
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ...packages.shared.models import Meeting

router = APIRouter(prefix="/meetings", tags=["slides"])

STORAGE = Path("storage")

def _meeting_dir(mid: int) -> Path:
    return STORAGE / str(mid)

@router.post("/{meeting_id}/slides")
async def upload_slides(
    meeting_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    d = _meeting_dir(meeting_id)
    d.mkdir(parents=True, exist_ok=True)

    saved = []
    for uf in files:
        # basic filename guard
        name = Path(uf.filename).name
        dest = d / name
        with dest.open("wb") as out:
            while chunk := await uf.read(1024 * 1024):
                out.write(chunk)
        saved.append(name)
    return {"meeting_id": meeting_id, "saved": saved}

@router.get("/{meeting_id}/slides.zip")
def download_slides_zip(meeting_id: int):
    d = _meeting_dir(meeting_id)
    if not d.exists():
        raise HTTPException(status_code=404, detail="No slides uploaded")
    zpath = d / "slides.zip"
    with ZipFile(zpath, "w", ZIP_DEFLATED) as z:
        for p in d.iterdir():
            if p.name == "slides.zip" or not p.is_file():
                continue
            z.write(p, arcname=p.name)
    return FileResponse(zpath, media_type="application/zip", filename=f"meeting-{meeting_id}-slides.zip")
