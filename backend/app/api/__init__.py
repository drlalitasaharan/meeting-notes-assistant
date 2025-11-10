from fastapi import APIRouter

from .jobs import router as jobs_router

api = APIRouter(prefix="/v1")
api.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
