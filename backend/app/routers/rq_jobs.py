from fastapi import APIRouter, HTTPException
from rq.job import Job

from app.jobs.queue import get_redis

router = APIRouter(prefix="/v1/rq", tags=["rq"])


@router.get("/jobs/{rq_id}")
def read_rq_job(rq_id: str):
    try:
        j = Job.fetch(rq_id, connection=get_redis())
    except Exception:
        raise HTTPException(status_code=404, detail="Not Found")
    return {
        "id": j.id,
        "status": j.get_status(refresh=True),
        "meta": j.meta,
        "result": getattr(j, "result", None),
    }
