from __future__ import annotations
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, Response, HTTPException
from fastapi.responses import FileResponse

from ..deps import require_api_key

# IMPORTANT: prefix is just "/meetings".
# main.py will include this router with prefix="/v1".
router = APIRouter(prefix="/meetings", tags=["slides"])

STORAGE_DIR = Path("storage")


def _meeting_dir(mid: int) -> Path:
    return STORAGE_DIR / f"meeting_{mid}"


@router.post("/{meeting_id}/slides")
async def upload_slides(
    meeting_id: int,
    files: List[UploadFile] = File(...),
    _: None = Depends(require_api_key),
):
    dest = _meeting_dir(meeting_id)
    dest.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []

    for f in files:
        # guard the filename
        name = Path(f.filename).name
        data = await f.read()
        (dest / name).write_bytes(data)
        saved.append(name)

    return {"uploaded": saved}


@router.get("/{meeting_id}/slides")
def list_slides(meeting_id: int, _: None = Depends(require_api_key)):
    dest = _meeting_dir(meeting_id)
    if not dest.exists():
        return Response(status_code=204)
    files = sorted([p.name for p in dest.iterdir() if p.is_file()])
    if not files:
        return Response(status_code=204)
    return {"files": files}


@router.get("/{meeting_id}/slides/{filename}")
def get_slide_file(meeting_id: int, filename: str, _: None = Depends(require_api_key)):
    p = _meeting_dir(meeting_id) / Path(filename).name
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    mt = "text/plain" if p.suffix.lower() == ".txt" else "application/octet-stream"
    return FileResponse(p, media_type=mt, filename=p.name)

