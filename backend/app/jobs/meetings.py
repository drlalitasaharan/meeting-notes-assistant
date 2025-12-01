"""RQ job wiring for meeting processing."""

from __future__ import annotations

from app.jobs.queue import queue


def process_meeting(meeting_id: int) -> None:
    """Thin wrapper delegating to app.jobs.process_meeting.process_meeting."""
    # Local import to avoid circular imports at module import time
    from app.jobs.process_meeting import process_meeting as _impl

    # Underlying implementation expects meeting_id as str
    _impl(meeting_id=str(meeting_id))


def enqueue_process_meeting(meeting_id: int):
    """Enqueue the meeting for async processing via RQ.

    This wraps the shared process_meeting(meeting_id) job so the
    API, tests, and worker all share the same logic.
    """
    job = queue.enqueue(
        process_meeting,
        meeting_id=meeting_id,
        description=f"process_meeting[{meeting_id}]",
        job_timeout="30m",
    )
    return job
