import re

def summarize_simple(text: str, sentences: int = 3) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    bullets = [(ln[2:].strip() if ln.startswith(("- ", "* ")) else ln)
               for ln in lines if ln.startswith(("- ", "* "))]
    if bullets:
        return " ".join(bullets[:max(1, sentences)])
    chunks = re.split(r'(?<=[.!?])\s+', " ".join(lines))
    chunks = [c.strip() for c in chunks if c.strip()]
    return " ".join(chunks[:max(1, sentences)])
