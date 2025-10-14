# backend/packages/shared/minio_client.py
from __future__ import annotations

import logging
from contextlib import suppress
from typing import IO

import boto3
from botocore.client import BaseClient

from packages.shared.env import settings

log = logging.getLogger(__name__)

RAW_BUCKET = getattr(settings, "S3_BUCKET_RAW", "raw")
SLIDES_BUCKET = getattr(settings, "S3_BUCKET_SLIDES", "slides")

_s3: BaseClient | None = None


def _client() -> BaseClient:
    global _s3
    if _s3 is None:
        _s3 = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=getattr(settings, "S3_REGION", None),
        )
    return _s3


def _ensure_bucket(bucket: str) -> None:
    s3 = _client()
    with suppress(Exception):
        s3.head_bucket(Bucket=bucket)
        return
    # If head_bucket failed, try create (idempotent-ish)
    with suppress(Exception):
        s3.create_bucket(Bucket=bucket)


# Best-effort warmup so first request doesn't pay bucket creation cost
for _bucket in (RAW_BUCKET, SLIDES_BUCKET):
    with suppress(Exception):
        _ensure_bucket(_bucket)


def presign_get(key: str, expires: int = 900, bucket: str | None = None) -> str:
    """Generate a presigned GET URL for downloading an object (SigV4)."""
    _bucket = bucket or (SLIDES_BUCKET if key.startswith("slides/") else RAW_BUCKET)
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": _bucket, "Key": key},
        ExpiresIn=expires,
    )


def presign_put(
    key: str,
    bucket: str = RAW_BUCKET,
    content_type: str | None = None,
) -> str:
    """Generate a presigned PUT URL for uploading an object."""
    params: dict[str, str] = {"Bucket": bucket, "Key": key}
    if content_type:
        params["ContentType"] = content_type
    return _client().generate_presigned_url(
        "put_object",
        Params=params,
        ExpiresIn=900,
    )


def upload_fileobj(
    fp: IO[bytes],
    key: str,
    bucket: str = RAW_BUCKET,
    content_type: str | None = None,
) -> None:
    """Upload a file-like object to a bucket/key."""
    extra_args: dict[str, str] = {}
    if content_type:
        extra_args["ContentType"] = content_type
    _client().upload_fileobj(fp, bucket, key, ExtraArgs=extra_args)


def object_exists(key: str, bucket: str | None = None) -> bool:
    """Return True if the object exists."""
    _bucket = bucket or (SLIDES_BUCKET if key.startswith("slides/") else RAW_BUCKET)
    try:
        _client().head_object(Bucket=_bucket, Key=key)
        return True
    except Exception:
        return False


def list_keys(prefix: str, bucket: str, max_keys: int = 1000) -> list[str]:
    """
    List object keys under a prefix. Handles pagination if needed.
    """
    _ensure_bucket(bucket)
    keys: list[str] = []
    token: str | None = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix, "MaxKeys": max_keys}
        if token:
            kwargs["ContinuationToken"] = token  # type: ignore[assignment]
        resp = _client().list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []) or []:
            k = obj.get("Key")
            if k:
                keys.append(k)
        if not resp.get("IsTruncated"):
            break
        token = resp.get("NextContinuationToken")
        if not token:
            break
    return keys
