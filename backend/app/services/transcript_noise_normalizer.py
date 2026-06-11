from __future__ import annotations

import re

_ACRONYM_REPLACEMENTS = {
    "l_c_d_": "LCD",
    "t_v_": "TV",
    "d_v_d_": "DVD",
    "m_p_e_g_": "MPEG",
    "x_m_l_": "XML",
    "l_s_a_": "LSA",
    "u_i_": "UI",
    "u_x_": "UX",
    "a_p_i_": "API",
}


_PHRASE_REPLACEMENTS = {
    "remote-controller": "remote control",
    "remote controller": "remote control",
    "touch screen": "touchscreen",
    "two digit": "two-digit",
    "one digit": "one-digit",
    "follow up": "follow-up",
    "stand by": "standby",
}


_NOISE_PATTERNS = [
    r"\[(?:inaudible|unintelligible|crosstalk|music|noise|silence)\]",
    r"\((?:inaudible|unintelligible|crosstalk|music|noise|silence)\)",
    r"\b(?:um+|uh+|erm+|hmm+)\b",
]


def normalize_transcript_for_regression(transcript: str | None) -> str:
    """Normalize noisy transcript text before regression extraction.

    This preserves original casing and names, because owner extraction and some
    regression tests depend on casing such as "Priya" and "Pricing confirmation".
    """

    if not transcript:
        return ""

    text = transcript

    # Normalize unicode punctuation and whitespace-like artifacts.
    text = text.replace("\u2019", "'")
    text = text.replace("\u2018", "'")
    text = text.replace("\u201c", '"')
    text = text.replace("\u201d", '"')
    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "-")
    text = text.replace("\u00a0", " ")

    # Normalize common underscore-style acronym artifacts.
    for source, target in _ACRONYM_REPLACEMENTS.items():
        text = re.sub(re.escape(source), target, text, flags=re.IGNORECASE)

    # Normalize phrase artifacts without lowercasing the whole transcript.
    for source, target in _PHRASE_REPLACEMENTS.items():
        text = re.sub(re.escape(source), target, text, flags=re.IGNORECASE)

    # Collapse spaced-out common acronyms seen in rough transcripts.
    text = re.sub(r"\bl\s*c\s*d\b", "LCD", text, flags=re.IGNORECASE)
    text = re.sub(r"\bt\s*v\b", "TV", text, flags=re.IGNORECASE)
    text = re.sub(r"\bd\s*v\s*d\b", "DVD", text, flags=re.IGNORECASE)
    text = re.sub(r"\bm\s*p\s*e\s*g\b", "MPEG", text, flags=re.IGNORECASE)
    text = re.sub(r"\bx\s*m\s*l\b", "XML", text, flags=re.IGNORECASE)
    text = re.sub(r"\bl\s*s\s*a\b", "LSA", text, flags=re.IGNORECASE)

    for pattern in _NOISE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    # Keep sentence separators useful while removing repeated symbols.
    text = re.sub(r"[|]+", ". ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()
