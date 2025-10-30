from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

router = APIRouter(prefix="/v1/dev", tags=["dev"])

BASE = Path(os.getenv("FS_STORAGE_DIR", "storage")).resolve()


@router.get("/object/{path:path}")
def dev_object(path: str, token: str = Query(...)):
    if token != "dev":
        raise HTTPException(status_code=403, detail="forbidden")
    p = (BASE / path).resolve()
    if not str(p).startswith(str(BASE)) or not p.exists():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(str(p))
