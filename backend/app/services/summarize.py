# backend/app/services/summarize.py


def summarize_text(text: str) -> str:
    # Minimal stub; replace with your provider.
    # Example OpenAI (uncomment after installing openai and setting OPENAI_API_KEY)
    """
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),
        messages=[{"role": "system","content":"Summarize the meeting transcript into bullet points of decisions and action items."},
                  {"role": "user","content": text[:12000]}]
    )
    return resp.choices[0].message.content.strip()
    """
    # Fallback local summary
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "• " + "\n• ".join(lines[:8])
