from __future__ import annotations

import logging
import math
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

from .base import Transcriber
from .schemas import TranscriptionResult, TranscriptionSegment

log = logging.getLogger(__name__)

DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY_SECONDS = 2.0
DEFAULT_CHUNK_THRESHOLD_SECONDS = 180 * 60
DEFAULT_CHUNK_SECONDS = 30 * 60


def _to_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return dict(value)


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value.strip())
    except ValueError:
        return default

    return max(1, value)


def _float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = float(raw_value.strip())
    except ValueError:
        return default

    return max(0.0, value)


def _probe_audio_duration_seconds(audio_path: str | Path) -> float | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return None

    try:
        duration = float(result.stdout.strip())
    except ValueError:
        return None

    if duration <= 0:
        return None

    return duration


def _write_audio_chunk(
    *,
    source_path: str | Path,
    output_path: str | Path,
    start_seconds: float,
    duration_seconds: float,
) -> None:
    timeout_seconds = max(120, int(duration_seconds * 2) + 60)

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{start_seconds:.3f}",
                "-t",
                f"{duration_seconds:.3f}",
                "-i",
                str(source_path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-b:a",
                "64k",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Failed to split transcription audio chunk at {start_seconds:.1f}s: "
            f"{exc.stderr or exc.stdout or exc}"
        ) from exc
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(
            f"Failed to split transcription audio chunk at {start_seconds:.1f}s"
        ) from exc


class OpenAIWhisperTranscriber(Transcriber):
    def __init__(self) -> None:
        self.model_name = os.getenv("OPENAI_TRANSCRIPTION_MODEL", "whisper-1")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.retry_attempts = _int_env(
            "OPENAI_TRANSCRIPTION_RETRY_ATTEMPTS",
            DEFAULT_RETRY_ATTEMPTS,
        )
        self.retry_delay_seconds = _float_env(
            "OPENAI_TRANSCRIPTION_RETRY_DELAY_SECONDS",
            DEFAULT_RETRY_DELAY_SECONDS,
        )
        self.chunk_threshold_seconds = _int_env(
            "OPENAI_TRANSCRIPTION_CHUNK_THRESHOLD_SECONDS",
            DEFAULT_CHUNK_THRESHOLD_SECONDS,
        )
        self.chunk_seconds = _int_env(
            "OPENAI_TRANSCRIPTION_CHUNK_SECONDS",
            DEFAULT_CHUNK_SECONDS,
        )

    def transcribe(self, audio_path: str | Path) -> TranscriptionResult:
        path = Path(audio_path)
        duration_seconds = _probe_audio_duration_seconds(path)

        if duration_seconds is not None and duration_seconds > self.chunk_threshold_seconds:
            return self._transcribe_long_audio_in_chunks(
                path,
                duration_seconds=duration_seconds,
            )

        return self._transcribe_single_file(path)

    def _transcribe_long_audio_in_chunks(
        self,
        audio_path: Path,
        *,
        duration_seconds: float,
    ) -> TranscriptionResult:
        chunk_count = math.ceil(duration_seconds / self.chunk_seconds)
        chunk_results: list[tuple[float, TranscriptionResult]] = []

        log.info(
            "openai transcription: chunking long audio",
            extra={
                "duration_seconds": duration_seconds,
                "chunk_seconds": self.chunk_seconds,
                "chunk_count": chunk_count,
            },
        )

        with tempfile.TemporaryDirectory(prefix="meetiq-transcription-chunks-") as tmpdir:
            tmpdir_path = Path(tmpdir)

            for index in range(chunk_count):
                start_seconds = float(index * self.chunk_seconds)
                remaining_seconds = duration_seconds - start_seconds
                if remaining_seconds <= 0:
                    break

                chunk_duration_seconds = min(
                    float(self.chunk_seconds),
                    remaining_seconds,
                )
                chunk_path = tmpdir_path / f"chunk_{index:04d}.mp3"

                _write_audio_chunk(
                    source_path=audio_path,
                    output_path=chunk_path,
                    start_seconds=start_seconds,
                    duration_seconds=chunk_duration_seconds,
                )

                log.info(
                    "openai transcription: transcribing chunk",
                    extra={
                        "chunk_index": index,
                        "chunk_count": chunk_count,
                        "chunk_start_seconds": start_seconds,
                        "chunk_duration_seconds": chunk_duration_seconds,
                    },
                )

                chunk_results.append(
                    (
                        start_seconds,
                        self._transcribe_single_file(chunk_path),
                    )
                )

        return self._combine_chunk_results(
            chunk_results,
            duration_seconds=duration_seconds,
        )

    def _transcribe_single_file(self, audio_path: Path) -> TranscriptionResult:
        last_error: Exception | None = None

        for attempt in range(1, self.retry_attempts + 1):
            try:
                return self._transcribe_once(audio_path)
            except Exception as exc:
                last_error = exc
                if attempt >= self.retry_attempts:
                    break

                log.warning(
                    "openai transcription: retrying after error",
                    extra={
                        "attempt": attempt,
                        "max_attempts": self.retry_attempts,
                        "audio_filename": audio_path.name,
                        "error": str(exc),
                    },
                )

                if self.retry_delay_seconds > 0:
                    time.sleep(self.retry_delay_seconds)

        if last_error is not None:
            raise last_error

        raise RuntimeError("OpenAI transcription failed without an exception")

    def _transcribe_once(self, audio_path: Path) -> TranscriptionResult:
        with audio_path.open("rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=self.model_name,
                file=audio_file,
                response_format="verbose_json",
            )

        return self._result_from_response(response)

    def _result_from_response(self, response: Any) -> TranscriptionResult:
        data = _to_dict(response)

        segments: list[TranscriptionSegment] = []
        for seg in data.get("segments") or []:
            seg_dict = _to_dict(seg)
            text = str(seg_dict.get("text") or "").strip()
            if not text:
                continue

            segments.append(
                TranscriptionSegment(
                    start=float(seg_dict.get("start") or 0.0),
                    end=float(seg_dict.get("end") or 0.0),
                    text=text,
                )
            )

        return TranscriptionResult(
            text=str(data.get("text") or "").strip(),
            language=data.get("language"),
            duration_seconds=data.get("duration"),
            segments=segments,
            model_name=self.model_name,
        )

    def _combine_chunk_results(
        self,
        chunk_results: list[tuple[float, TranscriptionResult]],
        *,
        duration_seconds: float,
    ) -> TranscriptionResult:
        text_parts: list[str] = []
        segments: list[TranscriptionSegment] = []
        language: str | None = None

        for offset_seconds, chunk_result in chunk_results:
            if chunk_result.text.strip():
                text_parts.append(chunk_result.text.strip())

            if language is None and chunk_result.language:
                language = str(chunk_result.language)

            for segment in chunk_result.segments:
                segments.append(
                    TranscriptionSegment(
                        start=segment.start + offset_seconds,
                        end=segment.end + offset_seconds,
                        text=segment.text,
                    )
                )

        return TranscriptionResult(
            text="\n\n".join(text_parts).strip(),
            language=language,
            duration_seconds=duration_seconds,
            segments=segments,
            model_name=self.model_name,
        )
