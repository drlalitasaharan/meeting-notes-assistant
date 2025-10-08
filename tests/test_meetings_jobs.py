import time

import httpx

API = "http://127.0.0.1:8000/v1"
H = {"X-API-Key": "dev-secret-123"}
TIMEOUT = httpx.Timeout(10.0, connect=5.0)


def test_meetings_crud_and_search():
    with httpx.Client(timeout=TIMEOUT) as c:
        r = c.post(f"{API}/meetings", headers=H, params={"title": "Test Sync", "tags": "qa,smoke"})
        assert r.status_code == 200
        mid = r.json()["id"]

        r = c.get(f"{API}/meetings", headers=H, params={"query": "sync"})
        assert r.status_code == 200
        assert any(it["id"] == mid for it in r.json()["items"])


def test_jobs_flow():
    with httpx.Client(timeout=TIMEOUT) as c:
        # assume meeting 1 exists
        r = c.post(f"{API}/jobs", headers=H, params={"type": "process_meeting", "meeting_id": 1})
        assert r.status_code == 201
        jid = r.json()["id"]

        # poll
        for _ in range(20):
            g = c.get(f"{API}/jobs/{jid}", headers=H)
            assert g.status_code == 200
            if g.json()["status"] in ("done", "failed"):
                break
            time.sleep(0.2)

        logs = c.get(f"{API}/jobs/{jid}/logs", headers=H)
        assert logs.status_code == 200
        assert "done" in logs.text

