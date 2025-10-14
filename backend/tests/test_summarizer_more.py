from app.summarizers import summarize_simple

def test_prefers_bullets_exact_n():
    text = "title\n- A\n- B\n- C\n"
    assert summarize_simple(text, sentences=2) == "A B"

def test_paragraph_split_basic():
    out = summarize_simple("One. Two. Three.", sentences=2)
    assert "One." in out and "Two." in out and "Three." not in out

def test_empty_input():
    assert summarize_simple("", sentences=3) == ""

def test_unicode_punct():
    out = summarize_simple("Hello… world! New? Line.", sentences=2)
    assert out
