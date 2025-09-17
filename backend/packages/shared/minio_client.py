# backend/packages/shared/minio_client.py
import logging
from typing import IO, List, Optional

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import ClientError

from packages.shared.env import settings

logger = logging.getLogger(__name__)

# Buckets from settings (env-overridable via your Settings)
RAW_BUCKET = settings.RAW_BUCKET
SLIDES_BUCKET = settings.SLIDES_BUCKET


# --------------------------------------------------------------------
# Low-level client (MinIO is S3-compatible) with SigV4 + path-style
# --------------------------------------------------------------------
def _build_s3_client() -> BaseClient:
    """
    Build an S3-compatible client that:
      - Uses Signature V4 (required for modern MinIO)
      - Uses path-style addressing (http://host:9000/<bucket>/<key>)
    """
    scheme = "https" if settings.MINIO_USE_SSL else "http"
    endpoint_url = f"{scheme}://{settings.MINIO_ENDPOINT}"
    region = getattr(settings, "AWS_REGION", "us-east-1")

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name=region,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            retries={"max_attempts": 2, "mode": "standard"},
        ),
    )


_s3: Optional[BaseClient] = None


def s3() -> BaseClient:
    """Return a singleton boto3 S3 client."""
    global _s3
    if _s3 is None:
        _s3 = _build_s3_client()
    return _s3


def _ensure_bucket(bucket: str) -> None:
    """
    Ensure a bucket exists. If head_bucket fails, try to create it.
    Safe to call repeatedly; MinIO ignores create if it already exists.
    """
    try:
        s3().head_bucket(Bucket=bucket)
    except Exception:
        try:
            s3().create_bucket(Bucket=bucket)
        except Exception as e:
            # Log and continue — subsequent ops will error explicitly if needed
            logger.warning("create_bucket failed for %s: %s", bucket, e)


# Best-effort warmup so first request doesn't pay bucket creation cost
for _bucket in (RAW_BUCKET, SLIDES_BUCKET):
    try:
        _ensure_bucket(_bucket)
    except Exception:
        # non-fatal at import time
        pass


# --------------------------------------------------------------------
# Convenience helpers (now SigV4 presigned URLs)
# --------------------------------------------------------------------
def presign_put(key: str, expires: int = 3600, bucket: str = RAW_BUCKET) -> str:
    """Generate a presigned PUT URL for uploading an object (SigV4)."""
    logger.debug("presign_put bucket=%s key=%s expires=%s", bucket, key, expires)
    _ensure_bucket(bucket)
    return s3().generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=int(expires),
    )


def presign_get(key: str, expires: int = 900, bucket: Optional[str] = None) -> str:
    """Generate a presigned GET URL for downloading an object (SigV4)."""
    _bucket = bucket or (SLIDES_BUCKET if key.startswith("slides/") else RAW_BUCKET)
    logger.debug("presign_get bucket=%s key=%s expires=%s", _bucket, key, expires)
    _ensure_bucket(_bucket)
    return s3().generate_presigned_url(
        "get_object",
        Params={"Bucket": _bucket, "Key": key},
        ExpiresIn=int(expires),
    )


def upload_fileobj(
    fileobj: IO[bytes],
    key: str,
    bucket: str = RAW_BUCKET,
    content_type: Optional[str] = None,
) -> None:
    """Upload a file-like object to a bucket/key."""
    logger.debug("upload_fileobj bucket=%s key=%s", bucket, key)
    _ensure_bucket(bucket)
    extra = {"ContentType": content_type} if content_type else {}
    s3().upload_fileobj(fileobj, bucket, key, ExtraArgs=extra)


def object_exists(key: str, bucket: Optional[str] = None) -> bool:
    """Return True if the object exists."""
    _bucket = bucket or (SLIDES_BUCKET if key.startswith("slides/") else RAW_BUCKET)
    try:
        s3().head_object(Bucket=_bucket, Key=key)
        return True
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "Unknown")
        if code in ("404", "NoSuchKey", "NotFound"):
            return False
        logger.info("head_object unexpected error for %s/%s: %s", _bucket, key, code)
        return False
    except Exception as e:
        logger.info("head_object error for %s/%s: %s", _bucket, key, e)
        return False


def list_keys(prefix: str, bucket: str, max_keys: int = 1000) -> List[str]:
    """
    List object keys under a prefix. Handles pagination if needed.
    """
    _ensure_bucket(bucket)
    keys: List[str] = []
    token: Optional[str] = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix, "MaxKeys": max_keys}
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3().list_objects_v2(**kwargs)
        for c in resp.get("Contents", []) or []:
            keys.append(c["Key"])
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
        else:
            break
    return keys


# --------------------------------------------------------------------
# Slide-specific helper
# --------------------------------------------------------------------
def slides_object_key(meeting_id: str, filename: str = "slides.bin") -> str:
    """Standard object key for slides belonging to a meeting."""
    return f"slides/{meeting_id}/{filename}"

