import base64
import time
import requests
import streamlit as st

API = st.secrets.get("API_BASE", "http://127.0.0.1:8000/v1")
HEADERS = {"X-API-Key": st.secrets.get("API_KEY", "dev-secret-123")}

st.set_page_config(page_title="Meeting Notes Assistant", layout="wide")
st.title("Meeting Notes Assistant")

# --- quick create ------------------------------------------------------
with st.form("new-meeting"):
    c1, c2 = st.columns([3, 2])
    title = c1.text_input("Title")
    tags = c2.text_input("Tags (comma-separated)")
    create = st.form_submit_button("Create")
    if create:
        r = requests.post(f"{API}/meetings", headers=HEADERS, params={"title": title, "tags": tags})
        st.toast("Created!" if r.ok else f"Failed: {r.status_code}", icon="✅" if r.ok else "❌")
        st.experimental_rerun()

# --- helpers -----------------------------------------------------------
def status_chip(s: str) -> str:
    colors = {"new": "gray", "processing": "orange", "done": "green", "failed": "red", "queued": "blue", "running": "orange"}
    return f"<span style='padding:2px 8px;border-radius:12px;background:{colors.get(s,'gray')};color:white;font-size:12px'>{s}</span>"

def embed_pdf(b: bytes, height: int = 450):
    b64 = base64.b64encode(b).decode()
    st.components.v1.html(
        f"""
        <embed src="data:application/pdf;base64,{b64}" type="application/pdf" width="100%" height="{height}px" />
        """,
        height=height + 12,
    )

def list_meetings(query: str = "", tag: str = ""):
    r = requests.get(f"{API}/meetings", params={"query": query or None, "tag": tag or None, "page": 1, "limit": 50}, headers=HEADERS)
    r.raise_for_status()
    return r.json()["items"]

def list_files(mid: int):
    r = requests.get(f"{API}/meetings/{mid}/slides", headers=HEADERS)
    return r.json().get("files", []) if r.status_code == 200 else []

# --- controls ----------------------------------------------------------
colq, coltag = st.columns([3, 1])
with colq:
    query = st.text_input("Search meetings", "")
with coltag:
    tag = st.text_input("Tag filter", "")

items = list_meetings(query, tag)

# count + clear
c1, c2 = st.columns([1, 1])
with c1:
    st.caption(f"{len(items)} meeting(s) found)")
with c2:
    if st.button("Clear filters"):
        st.session_state.clear()
        st.experimental_rerun()

# --- list --------------------------------------------------------------
for m in items:
    with st.expander(f"#{m['id']} · {m['title']}"):
        st.markdown(f"**Status:** {status_chip(m['status'])}", unsafe_allow_html=True)
        st.write("**Tags:**", ", ".join(m["tags"]) or "—")

        upl = st.file_uploader("Upload slides (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=True, key=f"upl-{m['id']}")
        cols = st.columns(3)
        if upl and cols[0].button("Upload", key=f"upbtn-{m['id']}"):
            tosend = [("files", (f.name, f.getvalue())) for f in upl]
            r = requests.post(f"{API}/meetings/{m['id']}/slides", headers=HEADERS, files=tosend)
            if r.ok:
                st.success(f"Uploaded: {', '.join(r.json().get('saved', []))}")
            else:
                st.error(f"Upload failed: {r.status_code}")

        if cols[1].button("Process meeting", key=f"proc-{m['id']}"):
            r = requests.post(f"{API}/jobs", params={"type": "process_meeting", "meeting_id": m["id"]}, headers=HEADERS)
            if r.ok:
                st.session_state[f"job-{m['id']}"] = r.json()["id"]
            else:
                st.error("Failed to start job")

        if cols[2].button("Download slides.zip", key=f"zip-{m['id']}"):
            r = requests.get(f"{API}/meetings/{m['id']}/slides.zip", headers=HEADERS)
            if r.status_code == 200:
                st.download_button("Save ZIP", data=r.content, file_name=f"meeting-{m['id']}-slides.zip", mime="application/zip")
            else:
                st.warning("No slides uploaded yet.")

        # live job polling (if any)
        jid = st.session_state.get(f"job-{m['id']}")
        if jid:
            with st.status(f"Polling job #{jid}…", expanded=False) as s:
                for _ in range(24):
                    jr = requests.get(f"{API}/jobs/{jid}", headers=HEADERS).json()
                    logs = requests.get(f"{API}/jobs/{jid}/logs", headers=HEADERS).text
                    s.update(label=f"Job #{jid}: {jr['status']}")
                    if jr["status"] in ("done", "failed"):
                        break
                    time.sleep(0.5)
                st.code(logs)
                s.update(state="complete")

        # preview existing files
        files = list_files(m["id"])
        if files:
            st.write("**Files:**", ", ".join(files))
            for fn in files:
                r = requests.get(f"{API}/meetings/{m['id']}/slides/{fn}", headers=HEADERS)
                if r.status_code != 200:
                    continue
                if fn.lower().endswith(".txt"):
                    st.subheader(fn)
                    st.code(r.text, language="text")
                elif fn.lower().endswith(".pdf"):
                    st.subheader(fn)
                    embed_pdf(r.content, height=420)

