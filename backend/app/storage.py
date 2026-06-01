from __future__ import annotations

import io
import json
import os
from datetime import timedelta
from typing import Any, Dict

import boto3


def _bucket_name() -> str | None:
    return (
        os.getenv("S3_BUCKET")
        or os.getenv("AWS_S3_BUCKET")
        or os.getenv("S3_BUCKET_NAME")
        or os.getenv("OBJECT_BUCKET")
    )


def _region_name() -> str | None:
    return os.getenv("S3_REGION") or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")


class S3Storage:
    def __init__(self):
        self.bucket = _bucket_name()
        if not self.bucket:
            raise RuntimeError("S3 bucket is not configured")

        kwargs: dict[str, Any] = {}

        region = _region_name()
        if region:
            kwargs["region_name"] = region

        endpoint = os.getenv("S3_ENDPOINT") or os.getenv("AWS_ENDPOINT_URL")
        if endpoint:
            kwargs["endpoint_url"] = endpoint

        access = os.getenv("S3_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID")
        secret = os.getenv("S3_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
        if access and secret:
            kwargs["aws_access_key_id"] = access
            kwargs["aws_secret_access_key"] = secret

        self.client = boto3.client("s3", **kwargs)

    def put_json(self, key: str, obj: Dict[str, Any]) -> str:
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=io.BytesIO(payload),
            ContentType="application/json",
        )
        return key

    def sign_url(self, key: str, expires: int = 3600) -> str:
        expires_td = (
            timedelta(seconds=int(expires)) if isinstance(expires, (int, float)) else expires
        )
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=int(expires_td.total_seconds()),
        )


def choose_storage():
    backend = os.environ.get("STORAGE_BACKEND", "s3").lower()
    if backend == "s3":
        return S3Storage()
    raise RuntimeError(f"Unsupported STORAGE_BACKEND={backend!r}")


def health_check() -> dict:
    backend = os.getenv("STORAGE_BACKEND", "").lower()
    if backend != "s3":
        return {"status": "skipped"}

    try:
        storage = choose_storage()
        storage.client.head_bucket(Bucket=storage.bucket)
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "detail": f"storage health failed: {exc}"}
