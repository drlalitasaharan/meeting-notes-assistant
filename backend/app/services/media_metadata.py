from __future__ import annotations

import json
import subprocess
import tempfile


def probe_media_duration_seconds(
    data: bytes,
    *,
    suffix: str,
    timeout_seconds: int = 20,
) -> float | None:
    """
    Return media duration in seconds using ffprobe when available.

    Returns None if ffprobe is unavailable or duration cannot be detected.
    """
    normalized_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    if normalized_suffix == ".":
        normalized_suffix = ".bin"

    with tempfile.NamedTemporaryFile(suffix=normalized_suffix, delete=True) as tmp:
        tmp.write(data)
        tmp.flush()

        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "json",
                    tmp.name,
                ],
                capture_output=True,
                check=False,
                text=True,
                timeout=timeout_seconds,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            return None

    if result.returncode != 0:
        return None

    try:
        payload = json.loads(result.stdout or "{}")
        raw_duration = payload.get("format", {}).get("duration")
        duration = float(raw_duration)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None

    if duration <= 0:
        return None

    return duration
