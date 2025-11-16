def test_upload_slides_txt(client, api_headers):
    # create a meeting to attach slides to
    r = client.post(
        "/v1/meetings",
        json={"title": "Slides Test", "tags": "docs"},
        headers=api_headers,
    )
    assert r.status_code in (200, 201)
    mid = r.json()["id"]

    # upload a simple text "slide"
    files = [("files", ("hello.txt", b"hello", "text/plain"))]
    r2 = client.post(
        f"/v1/meetings/{mid}/slides",
        headers=api_headers,
        files=files,
    )
    assert r2.status_code in (200, 201)

    # list slides and ensure our file is present
    r3 = client.get(f"/v1/meetings/{mid}/slides", headers=api_headers)
    assert r3.status_code == 200
    body = r3.json()

    if isinstance(body, dict) and "items" in body:
        names = [
            it["filename"] if isinstance(it, dict) and "filename" in it else str(it)
            for it in body["items"]
        ]
    elif isinstance(body, list):
        names = [
            it["filename"] if isinstance(it, dict) and "filename" in it else str(it) for it in body
        ]
    else:
        names = []

    assert any("hello.txt" in n for n in names)
