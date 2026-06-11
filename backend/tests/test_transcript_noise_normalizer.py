from __future__ import annotations

from backend.app.services.transcript_noise_normalizer import normalize_transcript_for_regression


def test_normalizes_common_acronym_artifacts() -> None:
    transcript = "The L_C_D_ remote connects to the T_V_ and D_V_D_ player using M_P_E_G_ files."
    normalized = normalize_transcript_for_regression(transcript)
    lower = normalized.lower()

    assert "lcd" in lower
    assert "tv" in lower
    assert "dvd" in lower
    assert "mpeg" in lower
    assert "l_c_d_" not in lower


def test_normalizes_spaced_acronyms_and_phrases() -> None:
    transcript = "The l c d remote-controller has touch screen menus and two digit channels."
    normalized = normalize_transcript_for_regression(transcript)
    lower = normalized.lower()

    assert "lcd" in lower
    assert "remote control" in lower
    assert "touchscreen" in lower
    assert "two-digit" in lower


def test_removes_noise_markers_without_adding_content() -> None:
    transcript = "Um [inaudible] The team discussed X_M_L_ annotation data. Uh, next step."
    normalized = normalize_transcript_for_regression(transcript)
    lower = normalized.lower()

    assert "xml annotation data" in lower
    assert "inaudible" not in lower
    assert " um " not in f" {lower} "
    assert " uh " not in f" {lower} "


def test_preserves_names_and_sentence_casing() -> None:
    transcript = "Priya will send pricing. Pricing confirmation may delay the follow-up."
    normalized = normalize_transcript_for_regression(transcript)

    assert "Priya" in normalized
    assert "Pricing confirmation" in normalized
