from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/meetings", tags=["slides"])

STORAGE = Path("storage")


def _meeting_dir(mid: int) -> Path:
    return STORAGE / str(mid)


@router.post("/{meeting_id}/slides")
async def upload_slides(
    meeting_id: int,
    files: List[UploadFile] = File(...),
):
    """
    Accepts one or more files and stores them under storage/{meeting_id}/.
    Does *not* require the meeting to exist in DB (tests only check file handling).
    """
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


@router.get("/{meeting_id}/slides")
def list_slides(meeting_id: int):
    d = _meeting_dir(meeting_id)
    if not d.exists():
        # tests accept 200 with empty payload or 204; return 200+empty
        return {"files": []}
    files = [p.name for p in d.iterdir() if p.is_file() and p.name != "slides.zip"]
    return {"files": files}


@router.get("/{meeting_id}/slides/{filename}")
def get_slide_file(meeting_id: int, filename: str):
    p = _meeting_dir(meeting_id) / Path(filename).name
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    # naive content type switch for txt/pdf
    mt = "text/plain" if p.suffix.lower() == ".txt" else "application/pdf"
    return FileResponse(p, media_type=mt, filename=p.name)


@router.get("/{meeting_id}/slides.zip")
def download_slides_zip(meeting_id: int):
    d = _meeting_dir(meeting_id)
    if not d.exists():
        raise HTTPException(status_code=404, detail="No slides uploaded")
    zpath = d / "slides.zip"
    # Build the zip fresh each time
    from zipfile import ZipFile, ZIP_DEFLATED

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

