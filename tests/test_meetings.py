def test_create_and_list_meetings(client, api_headers):
    r1 = client.post(
        "/v1/meetings",
        params={"title": "Team Sync", "tags": "sprint,planning"},
        headers=api_headers,
    )
    r2 = client.post(
        "/v1/meetings",
        params={"title": "Design Review", "tags": "design"},
        headers=api_headers,
    )
    assert r1.status_code == 200 and r2.status_code == 200

    r = client.get("/v1/meetings", headers=api_headers, params={"query": "design"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert any("Design Review" in it["title"] for it in items)


def test_search_and_patch_meeting(client, api_headers):
    client.post(
        "/v1/meetings",
        params={"title": "Standup", "tags": "daily,team"},
        headers=api_headers,
    )
    client.post(
        "/v1/meetings",
        params={"title": "Design Review", "tags": "design,ux"},
        headers=api_headers,
    )

    r = client.get("/v1/meetings", headers=api_headers, params={"query": "design"})
    assert r.status_code == 200
    items = r.json()["items"]
    mid = items[0]["id"]

    # patch tags
    r = client.patch(
        f"/v1/meetings/{mid}",
        headers=api_headers,
        params={"tags": "ops,retro,closeout"},
    )
    assert r.status_code == 200


def test_meeting_crud_minimal(client, api_headers):
    # create
    r = client.post(
        "/v1/meetings",
        params={"title": "Retro", "tags": "ops,retro"},
        headers=api_headers,
    )
    assert r.status_code == 200
    mid = r.json()["id"]

    # get
    r = client.get(f"/v1/meetings/{mid}", headers=api_headers)
    assert r.status_code == 200

