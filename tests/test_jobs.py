def test_enqueue_and_inspect_job(client, api_headers):
    # Need a meeting to reference
    r = client.post(
        "/v1/meetings",
        params={"title": "Test Sync", "tags": "qa,smoke"},
        headers=api_headers,
    )
    assert r.status_code == 200
    mid = r.json()["id"]

    # enqueue
    r = client.post(
        "/v1/jobs",
        headers=api_headers,
        params={"type": "process_meeting", "meeting_id": mid},
    )
    assert r.status_code == 200
    jid = r.json()["id"]

    g = client.get(f"/v1/jobs/{jid}", headers=api_headers)
    assert g.status_code == 200

    logs = client.get(f"/v1/jobs/{jid}/logs", headers=api_headers)
    assert logs.status_code == 200

