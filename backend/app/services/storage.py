from __future__ import annotations

import os
import time
from pathlib import Path
from typing import BinaryIO, Optional, Protocol

import boto3
from botocore.client import Config


class Storage(Protocol):
    def put(self, key: str, body: BinaryIO, content_type: str) -> None: ...
    def presign_get(self, key: str, ttl: int = 3600) -> str: ...
    def exists(self, key: str) -> bool: ...


class FSStorage:
    """DEV-ONLY filesystem storage."""

    def __init__(self, base_dir: str = "storage"):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.base / key

    def put(self, key: str, body: BinaryIO, content_type: str) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            f.write(body.read())

    def presign_get(self, key: str, ttl: int = 3600) -> str:
        return f"http://localhost:8000/v1/dev/object/{key}?token=dev&t={int(time.time()) + ttl}"

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


class S3Storage:
    def __init__(
        self,
        bucket: str,
        endpoint: Optional[str],
        region: str = "us-east-1",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        secure: bool = True,
    ):
        self.bucket = bucket
        session = boto3.session.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        self.client = session.client(
            "s3",
            endpoint_url=endpoint,
            config=Config(s3={"addressing_style": "path"}),
            use_ssl=secure,
            verify=secure,
        )

    def put(self, key: str, body: BinaryIO, content_type: str) -> None:
        self.client.upload_fileobj(
            Fileobj=body,
            Bucket=self.bucket,
            Key=key,
            ExtraArgs={"ContentType": content_type},
        )

    def presign_get(self, key: str, ttl: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=ttl
        )

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False


def choose_storage() -> Storage:
    env = os.getenv("ENV", "dev").lower()
    force_obj = os.getenv("FORCE_OBJECT_STORAGE", "0") == "1"
    backend = os.getenv("STORAGE_BACKEND", "s3").lower()

    if env != "prod" and backend == "fs" and not force_obj:
        return FSStorage(base_dir=os.getenv("FS_STORAGE_DIR", "storage"))

    return S3Storage(
        bucket=os.environ["OBJECT_BUCKET"],
        endpoint=os.getenv("S3_ENDPOINT"),
        region=os.getenv("S3_REGION", "us-east-1"),
        access_key=os.getenv("S3_ACCESS_KEY"),
        secret_key=os.getenv("S3_SECRET_KEY"),
        secure=os.getenv("S3_SECURE", "true").lower() == "true",
    )
