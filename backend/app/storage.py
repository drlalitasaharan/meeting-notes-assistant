from __future__ import annotations

import io
import json
import os
from datetime import timedelta
from typing import Any, Dict
from urllib.parse import urlparse, urlunparse

from minio import Minio


class S3Storage:
    def __init__(self):
        self.bucket = os.environ.get("OBJECT_BUCKET", "mna-artifacts")
        endpoint = os.environ.get("S3_ENDPOINT", "http://minio:9000")
        access = os.environ.get("S3_ACCESS_KEY", "miniouser")
        secret = os.environ.get("S3_SECRET_KEY", "miniopass")
        secure = os.environ.get("S3_SECURE", "false").lower() in ("1", "true", "yes")

        netloc = urlparse(endpoint).netloc or endpoint.replace("http://", "").replace(
            "https://", ""
        )
        self.client = Minio(netloc, access_key=access, secret_key=secret, secure=secure)

    def put_json(self, key: str, obj: Dict[str, Any]) -> str:
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.client.put_object(
            self.bucket,
            key,
            io.BytesIO(payload),
            length=len(payload),
            content_type="application/json",
        )
        return key

    def sign_url(self, key: str, expires: int = 3600) -> str:
        # normalize to timedelta without changing the param type
        expires_td: timedelta
        if isinstance(expires, (int, float)):
            expires_td = timedelta(seconds=int(expires))
        else:
            # allow already-provided timedelta
            expires_td = expires  # type: ignore[assignment]

        url = self.client.presigned_get_object(self.bucket, key, expires=expires_td)
        public = os.environ.get("S3_PUBLIC_ENDPOINT")  # e.g. http://127.0.0.1:9000
        if public:
            u = urlparse(url)
            p = urlparse(public)
            url = urlunparse(
                (p.scheme or u.scheme, p.netloc or u.netloc, u.path, u.params, u.query, u.fragment)
            )
        return url


def choose_storage():
    backend = os.environ.get("STORAGE_BACKEND", "s3").lower()
    if backend == "s3":
        return S3Storage()
    raise RuntimeError(f"Unsupported STORAGE_BACKEND={backend!r}")


def health_check() -> dict:
    """Check readiness of the configured storage backend.

    For S3/MinIO backends we perform a cheap operation against the API.
    For local/dummy backends we report "skipped" so /healthz still returns a
    structured check.
    """
    backend = os.getenv("STORAGE_BACKEND", "").lower()
    # Avoid blowing up tests / local dev when using a non-S3 backend.
    if backend not in {"s3", "minio", "s3-minio"}:
        return {"status": "skipped"}

    try:
        storage = choose_storage()
        client = getattr(storage, "client", None) or getattr(storage, "_client", None)
        if client is None:
            return {
                "status": "skipped",
                "detail": "storage backend has no client attached",
            }

        # MinIO and boto3 S3 both expose list_buckets(), which is a cheap API ping.
        list_buckets = getattr(client, "list_buckets", None)
        if list_buckets is None:
            return {
                "status": "skipped",
                "detail": "storage client has no list_buckets() method",
            }

        list_buckets()
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        # Last-resort catch-all so /healthz never 500s because of storage.
        return {"status": "error", "detail": f"storage health failed: {exc}"}
