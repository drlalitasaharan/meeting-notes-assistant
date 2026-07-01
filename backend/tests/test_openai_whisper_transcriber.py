from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from app.services.transcription import openai_whisper


class _FakeTranscriptions:
    def __init__(self, *, failures_before_success: int = 0) -> None:
        self.failures_before_success = failures_before_success
        self.calls: list[str] = []

    def create(
        self,
        *,
        model: str,
        file: BinaryIO,
        response_format: str,
    ) -> dict[str, object]:
        del model, response_format

        self.calls.append(Path(file.name).name)

        if self.failures_before_success > 0:
            self.failures_before_success -= 1
            raise RuntimeError("temporary provider failure")

        stem = Path(file.name).stem
        return {
            "text": f"text for {stem}",
            "language": "en",
            "duration": 10.0,
            "segments": [
                {
                    "start": 1.0,
                    "end": 2.0,
                    "text": f"segment for {stem}",
                }
            ],
        }


class _FakeAudio:
    def __init__(self, transcriptions: _FakeTranscriptions) -> None:
        self.transcriptions = transcriptions


class _FakeClient:
    def __init__(self, transcriptions: _FakeTranscriptions) -> None:
        self.audio = _FakeAudio(transcriptions)


def _patch_openai_client(monkeypatch, transcriptions: _FakeTranscriptions) -> None:
    monkeypatch.setattr(
        openai_whisper,
        "OpenAI",
        lambda api_key: _FakeClient(transcriptions),
    )


def test_openai_whisper_retries_transient_transcription_errors(
    tmp_path,
    monkeypatch,
):
    audio_path = tmp_path / "meeting.mp3"
    audio_path.write_bytes(b"fake audio")

    transcriptions = _FakeTranscriptions(failures_before_success=1)
    _patch_openai_client(monkeypatch, transcriptions)

    monkeypatch.setenv("OPENAI_TRANSCRIPTION_RETRY_ATTEMPTS", "2")
    monkeypatch.setenv("OPENAI_TRANSCRIPTION_RETRY_DELAY_SECONDS", "0")
    monkeypatch.setenv("OPENAI_TRANSCRIPTION_CHUNK_THRESHOLD_SECONDS", "999999")
    monkeypatch.setattr(
        openai_whisper,
        "_probe_audio_duration_seconds",
        lambda audio_path: 60.0,
    )

    transcriber = openai_whisper.OpenAIWhisperTranscriber()
    result = transcriber.transcribe(audio_path)

    assert len(transcriptions.calls) == 2
    assert result.text == "text for meeting"
    assert result.segments[0].start == 1.0


def test_openai_whisper_chunks_long_audio_and_offsets_segments(
    tmp_path,
    monkeypatch,
):
    audio_path = tmp_path / "meeting.mp3"
    audio_path.write_bytes(b"fake audio")

    transcriptions = _FakeTranscriptions()
    _patch_openai_client(monkeypatch, transcriptions)

    monkeypatch.setenv("OPENAI_TRANSCRIPTION_RETRY_ATTEMPTS", "1")
    monkeypatch.setenv("OPENAI_TRANSCRIPTION_RETRY_DELAY_SECONDS", "0")
    monkeypatch.setenv("OPENAI_TRANSCRIPTION_CHUNK_THRESHOLD_SECONDS", "1800")
    monkeypatch.setenv("OPENAI_TRANSCRIPTION_CHUNK_SECONDS", "1800")
    monkeypatch.setattr(
        openai_whisper,
        "_probe_audio_duration_seconds",
        lambda audio_path: 5400.0,
    )

    def fake_write_audio_chunk(
        *,
        source_path: str | Path,
        output_path: str | Path,
        start_seconds: float,
        duration_seconds: float,
    ) -> None:
        del source_path, start_seconds, duration_seconds
        Path(output_path).write_bytes(b"fake chunk")

    monkeypatch.setattr(openai_whisper, "_write_audio_chunk", fake_write_audio_chunk)

    transcriber = openai_whisper.OpenAIWhisperTranscriber()
    result = transcriber.transcribe(audio_path)

    assert transcriptions.calls == [
        "chunk_0000.mp3",
        "chunk_0001.mp3",
        "chunk_0002.mp3",
    ]
    assert "text for chunk_0000" in result.text
    assert "text for chunk_0001" in result.text
    assert "text for chunk_0002" in result.text
    assert result.duration_seconds == 5400.0
    assert [segment.start for segment in result.segments] == [1.0, 1801.0, 3601.0]
    assert [segment.end for segment in result.segments] == [2.0, 1802.0, 3602.0]
