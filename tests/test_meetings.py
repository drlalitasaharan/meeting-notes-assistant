# tests/test_meetings.py
def test_health(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"ok": True}

def test_create_and_list_meetings(client, api_headers):
    # create two
    r1 = client.post("/v1/meetings", params={"title": "Sprint Planning", "tags": "sprint,planning"}, headers=api_headers)
    r2 = client.post("/v1/meetings", params={"title": "Design Review", "tags": "design"}, headers=api_headers)
    assert r1.status_code == 200 and r2.status_code == 200

    # list
    r = client.get("/v1/meetings", headers=api_headers, params={"page": 1, "limit": 10})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    titles = [m["title"] for m in body["items"]]
    assert "Sprint Planning" in titles and "Design Review" in titles

def test_query_and_tag_filter(client, api_headers):
    # seed
    client.post("/v1/meetings", params={"title": "Sprint Planning", "tags": "sprint,planning"}, headers=api_headers)
    client.post("/v1/meetings", params={"title": "Design Review", "tags": "design,ux"}, headers=api_headers)

    # query=design
    r = client.get("/v1/meetings", headers=api_headers, params={"query": "design"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1 and items[0]["title"] == "Design Review"

    # tag=ux
    r = client.get("/v1/meetings", headers=api_headers, params={"tag": "ux"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1 and items[0]["title"] == "Design Review"

def test_patch_status_and_tags(client, api_headers):
    # create
    r = client.post("/v1/meetings", params={"title": "Retro", "tags": "ops,retro"}, headers=api_headers)
    assert r.status_code == 200
    mid = r.json()["id"]

    # patch status
    r = client.patch(f"/v1/meetings/{mid}", headers=api_headers, params={"status": "done"})
    assert r.status_code == 200
    assert r.json()["status"] == "done"

    # patch tags
    r = client.patch(f"/v1/meetings/{mid}", headers=api_headers, params={"tags": "ops,retro,closeout"})
    assert r.status_code == 200
    assert r.json()["tags"] == ["ops", "retro", "closeout"]

