from rq.job import Job

from app.jobs.queue import get_redis


def _hydrate_artifact(job_row):
    try:
        r = get_redis()
        j = Job.fetch(job_row.id, connection=r)
    except Exception:
        return job_row

    status = j.get_status(refresh=True)
    artifact = (j.meta or {}).get("artifact_url") or getattr(j, "result", None)

    if status == "finished" and artifact and not getattr(job_row, "artifact_url", None):
        job_row.artifact_url = artifact
        job_row.status = "finished"
        try:
            from app.db import session

            with session() as s:
                s.add(job_row)
                s.commit()
        except Exception:
            pass

    if status == "failed" and getattr(job_row, "status", None) != "failed":
        job_row.status = "failed"
        try:
            from app.db import session

            with session() as s:
                s.add(job_row)
                s.commit()
        except Exception:
            pass
    return job_row
