from __future__ import annotations

from types import SimpleNamespace

from app.services.transcription import local_whisper


class FakeWhisperModel:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str]]] = []

    def transcribe(self, audio_path: str, **kwargs: str):
        self.calls.append((audio_path, kwargs))
        segments = [
            SimpleNamespace(start=0.0, end=1.0, text=" Hello "),
            SimpleNamespace(start=1.0, end=2.0, text=" world "),
        ]
        info = SimpleNamespace(language=kwargs.get("language"))
        return segments, info


def _install_fake_model(monkeypatch):
    created: list[FakeWhisperModel] = []

    def factory(*args, **kwargs):
        model = FakeWhisperModel()
        created.append(model)
        return model

    monkeypatch.setattr(local_whisper, "WhisperModel", factory)
    return created


def test_local_whisper_defaults_to_english(monkeypatch):
    monkeypatch.delenv("MEETIQ_TRANSCRIPTION_LANGUAGE", raising=False)
    monkeypatch.delenv("TRANSCRIPTION_LANGUAGE", raising=False)
    created = _install_fake_model(monkeypatch)

    transcriber = local_whisper.LocalWhisperTranscriber()
    result = transcriber.transcribe("meeting.mp3")

    assert created[0].calls == [("meeting.mp3", {"language": "en"})]
    assert result.language == "en"
    assert result.text == "Hello world"


def test_local_whisper_allows_auto_language_detection(monkeypatch):
    monkeypatch.setenv("MEETIQ_TRANSCRIPTION_LANGUAGE", "auto")
    monkeypatch.delenv("TRANSCRIPTION_LANGUAGE", raising=False)
    created = _install_fake_model(monkeypatch)

    transcriber = local_whisper.LocalWhisperTranscriber()
    result = transcriber.transcribe("meeting.mp3")

    assert created[0].calls == [("meeting.mp3", {})]
    assert result.language is None
    assert result.text == "Hello world"
