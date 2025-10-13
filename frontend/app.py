import streamlit as st, requests

API = st.secrets.get("API_BASE", "http://localhost:8000")

st.title("Meetings – Process & Notes")

mid = st.number_input("Meeting ID", min_value=1, step=1)
col1, col2, col3 = st.columns(3)

if col1.button("Process (OCR ➜ Summarize)"):
    r = requests.post(f"{API}/v1/meetings/{mid}/process", timeout=30)
    st.session_state["job_id"] = r.json()["job_id"]
    st.success(f"Enqueued job: {st.session_state['job_id']}")

if col2.button("Poll Job Status") and "job_id" in st.session_state:
    r = requests.get(f"{API}/v1/jobs/{st.session_state['job_id']}", timeout=15)
    st.write(r.json())

if col3.button("Load Notes"):
    r = requests.get(f"{API}/v1/meetings/{mid}/notes", timeout=15)
    data = r.json()
    st.subheader("Transcript snippet")
    st.code(data.get("transcript_snippet") or "—")
    st.subheader("Summary")
    st.code(data.get("summary_bullets") or "—")
