# tests/test_jobs.py
def test_enqueue_and_inspect_job(client, api_headers):
    # Need a meeting to reference
    r = client.post("/v1/meetings", params={"title": "Test Sync", "tags": "qa,smoke"}, headers=api_headers)
    assert r.status_code == 200
    mid = r.json()["id"]

    # enqueue
    r = client.post("/v1/jobs", headers=api_headers, params={"type": "process_meeting", "meeting_id": mid})
    assert r.status_code == 200
    job = r.json()
    jid = job["id"]
    assert job["type"] == "process_meeting"
    assert job["meeting_id"] == mid

    # list
    r = client.get("/v1/jobs", headers=api_headers)
    assert r.status_code == 200
    jobs = r.json()
    assert any(j["id"] == jid for j in jobs)

    # details
    r = client.get(f"/v1/jobs/{jid}", headers=api_headers)
    assert r.status_code == 200
    detail = r.json()
    assert detail["id"] == jid

    # logs (text/plain)
    r = client.get(f"/v1/jobs/{jid}/logs", headers=api_headers)
    assert r.status_code == 200
    assert "queued" in r.text

