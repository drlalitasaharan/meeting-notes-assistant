from __future__ import annotations


def test_healthz_shape(client):
    r = client.get("/healthz")
    assert r.status_code == 200

    payload = r.json()
    assert isinstance(payload, dict)
    assert "status" in payload
    assert "checks" in payload

    checks = payload["checks"]
    for key in ("db", "redis", "storage"):
        assert key in checks
        assert "status" in checks[key]
