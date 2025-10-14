import io

# backend/app/services/storage.py
import os
from pathlib import Path

from minio import Minio


def use_object_store() -> bool:
    return os.getenv("USE_OBJECT_STORAGE", "false").lower() == "true"


def minio_client() -> Minio:
    return Minio(
        os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minio"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minio123"),
        secure=os.getenv("MINIO_USE_SSL", "false").lower() == "true",
    )


def put_slide(meeting_id: int, filename: str, data: bytes) -> str:
    if use_object_store():
        bucket = os.getenv("SLIDES_BUCKET", "meeting-slides")
        mc = minio_client()
        if not mc.bucket_exists(bucket):
            mc.make_bucket(bucket)
        key = f"{meeting_id}/{Path(filename).name}"
        mc.put_object(bucket, key, data=io.BytesIO(data), length=len(data))
        return f"s3://{bucket}/{key}"
    else:
        d = Path("storage") / str(meeting_id)
        d.mkdir(parents=True, exist_ok=True)
        dst = d / Path(filename).name
        with open(dst, "wb") as f:
            f.write(data)
        return str(dst)
