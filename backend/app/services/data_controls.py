from __future__ import annotations

from urllib.parse import urlparse

from app.services.storage import choose_storage


def storage_key_from_raw_media_path(raw_media_path: str | None) -> str | None:
    if not raw_media_path:
        return None

    value = raw_media_path.strip()
    if not value:
        return None

    if value.startswith("s3://"):
        parsed = urlparse(value)
        key = parsed.path.lstrip("/")
        return key or None

    if value.startswith("http://") or value.startswith("https://"):
        return None

    return value.lstrip("/") or None


def delete_raw_media_best_effort(raw_media_path: str | None) -> bool:
    key = storage_key_from_raw_media_path(raw_media_path)
    if not key:
        return False

    try:
        choose_storage().delete(key)
    except Exception:
        return False

    return True
