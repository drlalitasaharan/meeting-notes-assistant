import io
import time
import json
import requests
import streamlit as st

API = "http://127.0.0.1:8000/v1"
HEADERS = {"X-API-Key": "dev-secret-123"}

st.set_page_config(page_title="Meeting Notes Assistant", layout="wide")
st.title("Meeting Notes Assistant")

# Search/filter
colq, coltag = st.columns([3,1])
with colq:
    query = st.text_input("Search meetings", "")
with coltag:
    tag = st.text_input("Tag filter", "")

resp = requests.get(f"{API}/meetings", params={"query": query or None, "tag": tag or None, "page": 1, "limit": 50}, headers=HEADERS)
data = resp.json()

# List
for m in data["items"]:
    with st.expander(f"#{m['id']} · {m['title']}"):
        st.write("Status:", m["status"])
        st.write("Tags:", ", ".join(m["tags"]) or "—")

        # Upload slides
        files = st.file_uploader("Upload slides (PDF/TXT)", type=["pdf","txt"], accept_multiple_files=True, key=f"up-{m['id']}")
        if files and st.button("Upload", key=f"btn-{m['id']}"):
            tosend = [("files", (f.name, f.getvalue())) for f in files]
            r = requests.post(f"{API}/meetings/{m['id']}/slides", headers=HEADERS, files=tosend)
            st.success(r.json())

        # Start processing job
        if st.button("Process meeting", key=f"proc-{m['id']}"):
            r = requests.post(f"{API}/jobs", params={"type": "process_meeting", "meeting_id": m["id"]}, headers=HEADERS)
            job = r.json()
            st.session_state[f"job-{m['id']}"] = job["id"]

        # Poll job status
        jid = st.session_state.get(f"job-{m['id']}")
        if jid:
            ph = st.empty()
            for _ in range(20):
                jr = requests.get(f"{API}/jobs/{jid}", headers=HEADERS).json()
                logs = requests.get(f"{API}/jobs/{jid}/logs", headers=HEADERS).text
                ph.info(f"Job {jid}: {jr['status']}")
                st.code(logs)
                if jr["status"] in ("done", "failed"):
                    break
                time.sleep(0.5)

        # Preview PDFs/TXT (basic)
        if st.button("Download slides.zip", key=f"zip-{m['id']}"):
            r = requests.get(f"{API}/meetings/{m['id']}/slides.zip", headers=HEADERS)
            if r.status_code == 200:
                st.download_button("Save ZIP", data=r.content, file_name=f"meeting-{m['id']}-slides.zip")
            else:
                st.warning("No slides uploaded yet.")
