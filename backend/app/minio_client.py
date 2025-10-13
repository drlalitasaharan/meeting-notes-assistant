from minio import Minio

from .core.settings import settings


def get_minio() -> Minio | None:
    if (
        not settings.MINIO_ENDPOINT
        or not settings.MINIO_ACCESS_KEY
        or not settings.MINIO_SECRET_KEY
    ):
        return None
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )
