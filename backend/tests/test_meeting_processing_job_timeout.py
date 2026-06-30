from app.jobs import meetings


class FakeQueue:
    def __init__(self) -> None:
        self.kwargs = {}

    def enqueue(self, *args, **kwargs):
        self.kwargs = kwargs
        return {"id": "fake-job"}


def test_processing_job_timeout_defaults_to_four_hours(monkeypatch):
    monkeypatch.delenv("MEETIQ_PROCESSING_JOB_TIMEOUT_SECONDS", raising=False)

    assert meetings.processing_job_timeout_seconds() == 4 * 60 * 60


def test_processing_job_timeout_can_be_overridden(monkeypatch):
    monkeypatch.setenv("MEETIQ_PROCESSING_JOB_TIMEOUT_SECONDS", str(2 * 60 * 60))

    assert meetings.processing_job_timeout_seconds() == 2 * 60 * 60


def test_processing_job_timeout_uses_default_for_invalid_env(monkeypatch):
    monkeypatch.setenv("MEETIQ_PROCESSING_JOB_TIMEOUT_SECONDS", "not-a-number")

    assert meetings.processing_job_timeout_seconds() == 4 * 60 * 60


def test_enqueue_process_meeting_uses_configured_timeout(monkeypatch):
    fake_queue = FakeQueue()
    monkeypatch.setenv("MEETIQ_PROCESSING_JOB_TIMEOUT_SECONDS", str(3 * 60 * 60))
    monkeypatch.setattr(meetings, "queue", fake_queue)

    job = meetings.enqueue_process_meeting(meeting_id=123)

    assert job == {"id": "fake-job"}
    assert fake_queue.kwargs["meeting_id"] == 123
    assert fake_queue.kwargs["description"] == "process_meeting[123]"
    assert fake_queue.kwargs["job_timeout"] == 3 * 60 * 60
