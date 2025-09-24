# tests/test_slides.py
import io

def test_upload_slides_txt(client, api_headers):
    # create meeting
    r = client.post("/v1/meetings", params={"title": "Slides Test", "tags": "docs"}, headers=api_headers)
    assert r.status_code == 200
    mid = r.json()["id"]

    # upload a tiny .txt file
    files = [("files", ("readme.txt", io.BytesIO(b"hello world"), "text/plain"))]
    r = client.post(f"/v1/meetings/{mid}/slides", headers=api_headers, files=files)
    assert r.status_code == 200

    # list files (if supported)
    r = client.get(f"/v1/meetings/{mid}/slides", headers=api_headers)
    # Your router returns {"files":[...]} or 200/empty; accept either.
    assert r.status_code in (200, 204)

