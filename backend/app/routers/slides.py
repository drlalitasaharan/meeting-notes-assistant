from fastapi import APIRouter, UploadFile, File
router = APIRouter(prefix="/meetings", tags=["slides"])

@router.post("/{meeting_id}/slides")
async def upload_slides(meeting_id: int, files: list[UploadFile] = File(...)):
    # Stub: accept uploads and return filenames (no storage yet)
    return {"meeting_id": meeting_id, "uploaded": [f.filename for f in files]}
