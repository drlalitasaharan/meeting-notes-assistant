from __future__ import annotations


def test_meetings_crud_and_search(client, api_headers):
    # create a meeting via the in-process TestClient
    r = client.post(
        "/v1/meetings",
        headers=api_headers,
        json={"title": "Test Sync", "tags": "qa,smoke"},
    )
    assert r.status_code in (200, 201)
    body = r.json()
    mid = body["id"]

    # basic shape checks
    assert body["title"] == "Test Sync"
    assert "status" in body

    # search/filter for meetings via the API
    r2 = client.get(
        "/v1/meetings",
        headers=api_headers,
        params={"status": "new", "limit": 10, "offset": 0},
    )
    assert r2.status_code == 200
    data = r2.json()

    # backend now returns {"items": [...], "total": ...}
    items = data["items"] if isinstance(data, dict) and "items" in data else data

    # ensure our meeting is in the results
    assert any(m.get("id") == mid for m in items)
