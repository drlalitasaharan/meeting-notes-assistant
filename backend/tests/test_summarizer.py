from app.summarizers import summarize_simple

def test_summarizer_prefers_bullets():
    text = "title\n- A\n- B\n- C\n"
    out = summarize_simple(text, sentences=2)
    assert "A" in out and "B" in out and "C" not in out
