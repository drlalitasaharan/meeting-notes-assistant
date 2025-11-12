# app/routers/health.py

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz", operation_id="healthz")
def healthz():
    return {"status": "ok", "service": "meeting-notes-assistant", "version": "0.1.0"}


@router.head("/healthz", include_in_schema=False)
def healthz_head():
    from fastapi import Response

    return Response(status_code=200)
