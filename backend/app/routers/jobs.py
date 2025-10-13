import redis
from fastapi import APIRouter
from pydantic import BaseModel
from rq import Queue
from rq.job import Job

from ..core.settings import settings
from ..tasks import ocr_slides, summarize_meeting

router = APIRouter(prefix="/v1", tags=["jobs"])


class EnqueueResponse(BaseModel):
    job_id: str


@router.post("/meetings/{meeting_id}/process", response_model=EnqueueResponse)
def process_meeting(meeting_id: int):
    r = redis.from_url(settings.REDIS_URL)
    q = Queue(settings.RQ_QUEUE, connection=r)
    j1 = q.enqueue(ocr_slides, meeting_id, job_timeout=600)
    j2 = q.enqueue(summarize_meeting, meeting_id, depends_on=j1, job_timeout=600)
    return EnqueueResponse(job_id=j2.id)


class JobStatus(BaseModel):
    id: str
    status: str
    result: str | None = None


@router.get("/jobs/{job_id}", response_model=JobStatus)
def job_status(job_id: str):
    r = redis.from_url(settings.REDIS_URL)
    job = Job.fetch(job_id, connection=r)
    return JobStatus(
        id=job.id, status=job.get_status(), result=str(job.result) if job.is_finished else None
    )
