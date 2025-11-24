def enqueue_process_meeting(meeting_id: int):
    """
    Enqueue the meeting for async processing via RQ.

    This wraps the existing process_meeting(meeting_id) job so the
    API and tests can share the same logic.
    """
    # Local import to avoid circular imports at module import time
    from app.jobs.queue import queue

    return queue.enqueue(
        "app.jobs.meetings.process_meeting",  # use string path to avoid F821
        meeting_id=meeting_id,
        description=f"process_meeting[{meeting_id}]",
        job_timeout="30m",
    )
