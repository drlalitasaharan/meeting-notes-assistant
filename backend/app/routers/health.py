# app/routers/health.py
import os
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "service": os.getenv("APP_NAME", "meeting-notes-assistant"),
        "version": os.getenv("APP_VERSION", "0.1.0"),
    }

