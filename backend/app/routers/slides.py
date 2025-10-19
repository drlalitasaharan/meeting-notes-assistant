from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..core.settings import settings
from ..minio_client import get_minio

router = APIRouter(prefix="/v1/meetings", tags=["slides"])
STORAGE = Path("storage")


def _meeting_dir(mid: int) -> Path:
    return STORAGE / str(mid)


@router.post("/{meeting_id}/slides")
async def upload_slides(meeting_id: int, files: list[UploadFile] = File(...)):
    d = _meeting_dir(meeting_id)
    d.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for uf in files:
        if not uf.filename:
            continue
        name = Path(uf.filename).name
        dest = d / name
        with dest.open("wb") as w:
            w.write(await uf.read())
        saved.append(name)

        # Optional MinIO push
        m = get_minio()
        if m:
            if not m.bucket_exists(settings.SLIDES_BUCKET):
                m.make_bucket(settings.SLIDES_BUCKET)
            m.fput_object(settings.SLIDES_BUCKET, f"{meeting_id}/{name}", str(dest))
    return {"saved": saved, "count": len(saved)}


@router.get("/{meeting_id}/slides.zip")
def download_slides_zip(meeting_id: int):
    d = _meeting_dir(meeting_id)
    if not d.exists():
        raise HTTPException(status_code=404, detail="No slides for meeting")
    zpath = d.with_suffix(".zip")
    with ZipFile(zpath, "w", ZIP_DEFLATED) as zf:
        for p in d.iterdir():
            if p.is_file():
                zf.write(p, arcname=p.name)
    return FileResponse(str(zpath), filename=f"meeting_{meeting_id}_slides.zip")
