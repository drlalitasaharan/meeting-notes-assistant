from __future__ import annotations

import re
from typing import List


def _tail_with_overlap(text: str, overlap: int) -> str:
    if overlap <= 0 or len(text) <= overlap:
        return text
    return text[-overlap:]


def chunk_text(text: str, max_chars: int = 3500, overlap: int = 300) -> List[str]:
    if not text.strip():
        return []

    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)

        if len(para) <= max_chars:
            current = para
            continue

        start = 0
        while start < len(para):
            end = start + max_chars
            piece = para[start:end].strip()
            if piece:
                chunks.append(piece)
            if end >= len(para):
                break
            start = max(0, end - overlap)

        current = ""

    if current:
        chunks.append(current)

    return chunks
