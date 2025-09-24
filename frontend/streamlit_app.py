# frontend/streamlit_app.py

import os
import io
import base64
import time
import json
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

# -----------------------------------------------------------------------------
# Config (secrets first, then env, then defaults)
API = (
    st.secrets.get("API_BASE")
    or os.getenv("API_BASE_URL")
    or "http://127.0.0.1:8000/v1"
).rstrip("/")
API_KEY = st.secrets.get("API_KEY") or os.getenv("API_KEY") or "dev-secret-123"
HEADERS = {"X-API-Key": API_KEY}

st.set_page_config(page_title="Meeting Notes Assistant — MVP", layout="wide")
st.title("📝 Meeting Notes Assistant — MVP Test UI")
st.caption("Configure API in .streamlit/secrets.toml or environment variables if needed.")

# -----------------------------------------------------------------------------
# Helpers

def status_chip(s: str) -> str:
    colors = {"new": "#6b7280", "processing": "#d97706", "done": "#059669", "failed": "#dc2626", "queued": "#2563eb", "running": "#d97706"}
    return (
        f"<span style='padding:2px 8px;border-radius:12px;background:{colors.get(s,'#6b7280')};"
        "color:white;font-size:12px'>"
        f"{s}</span>"
    )

def embed_pdf(b: bytes, height: int = 450):
    b64 = base64.b64encode(b).decode()
    st.components.v1.html(
        f"""<embed src="data:application/pdf;base64,{b64}" type="application/pdf" width="100%" height="{height}px" />""",
        height=height + 12,
    )

def list_meetings(query: str = "", tag: str = "", page: int = 1, limit: int = 50):
    r = requests.get(f"{API}/meetings",
                     params={"query": query or None, "tag": tag or None, "page": page, "limit": limit},
                     headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def create_meeting(title: str, tags: str):
    r = requests.post(f"{API}/meetings", params={"title": title, "tags": tags or ""}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def patch_meeting(mid: int, *, title: Optional[str] = None, status: Optional[str] = None, tags: Optional[str] = None):
    r = requests.patch(f"{API}/meetings/{mid}", params={"title": title, "status": status, "tags": tags}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def list_files(mid: int) -> List[str]:
    r = requests.get(f"{API}/meetings/{mid}/slides", headers=HEADERS, timeout=30)
    if r.status_code == 200:
        data = r.json()
        # backend returns {"files": [...]}
        return data.get("files", data) if isinstance(data, dict) else data
    return []

def upload_slides(mid: int, files: List[st.runtime.uploaded_file_manager.UploadedFile]) -> Dict[str, Any]:
    tosend = [("files", (f.name, f.getvalue())) for f in files]
    r = requests.post(f"{API}/meetings/{mid}/slides", headers=HEADERS, files=tosend, timeout=120)
    r.raise_for_status()
    return r.json()

def download_zip(mid: int) -> Optional[bytes]:
    r = requests.get(f"{API}/meetings/{mid}/slides.zip", headers=HEADERS, timeout=60)
    if r.status_code == 200:
        return r.content
    return None

def start_job_process_meeting(mid: int) -> int:
    r = requests.post(f"{API}/jobs", params={"type": "process_meeting", "meeting_id": mid}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()["id"]

def get_job(jid: int) -> Dict[str, Any]:
    r = requests.get(f"{API}/jobs/{jid}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def get_job_logs(jid: int) -> str:
    r = requests.get(f"{API}/jobs/{jid}/logs", headers=HEADERS, timeout=30)
    # text/plain
    return r.text if r.status_code == 200 else ""


# -----------------------------------------------------------------------------
# New meeting form (top)
with st.form("new-meeting", clear_on_submit=True):
    c1, c2 = st.columns([3, 2])
    title = c1.text_input("Title", placeholder="e.g., Sprint Planning")
    tags_in = c2.text_input("Tags (comma-separated)", placeholder="sprint, planning")
    submitted = st.form_submit_button("➕ Create meeting")
    if submitted:
        if not title.strip():
            st.error("Title is required.")
        else:
            try:
                m = create_meeting(title.strip(), tags_in.strip())
                st.toast("Created ✅")
                # stash last created meeting id to auto-focus
                st.session_state["last_created_id"] = m["id"]
            except Exception as e:
                st.error(f"Create failed: {e}")

st.divider()

# -----------------------------------------------------------------------------
# Filters row
colq, coltag, colbtn = st.columns([3, 2, 1])
with colq:
    query = st.text_input("Search meetings", st.session_state.get("query", ""))
with coltag:
    tag = st.text_input("Tag filter", st.session_state.get("tag", ""))

with colbtn:
    if st.button("Clear filters"):
        st.session_state["query"] = ""
        st.session_state["tag"] = ""
        st.experimental_rerun()
    else:
        st.session_state["query"] = query
        st.session_state["tag"] = tag

# Load data
data = {}
try:
    data = list_meetings(query, tag, page=1, limit=50)
except Exception as e:
    st.error(f"Failed to load meetings: {e}")
    data = {"items": [], "page": 1, "limit": 50, "total": 0}

items = data.get("items", [])
st.caption(f"{len(items)} meeting(s) found")

# -----------------------------------------------------------------------------
# Meeting list
for m in items:
    mid = m["id"]
    with st.expander(f"#{mid} · {m['title']}"):
        # status & tags header
        st.markdown(f"**Status:** {status_chip(m['status'])}", unsafe_allow_html=True)
        st.write("**Tags:**", ", ".join(m["tags"]) or "—")

        # --- inline edit: status + tags (+ optional title) -------------------
        ec1, ec2, ec3, ec4 = st.columns([1.2, 2.0, 2.0, 1.0])
        new_status = ec1.selectbox(
            "Status",
            options=["new", "processing", "done", "failed"],
            index=["new", "processing", "done", "failed"].index(m["status"]),
            key=f"status-{mid}",
        )
        new_tags = ec2.text_input("Tags (comma-separated)", value=",".join(m["tags"]), key=f"tags-{mid}")
        new_title = ec3.text_input("Title (edit)", value=m["title"], key=f"title-{mid}")
        if ec4.button("Save", key=f"save-{mid}"):
            try:
                _ = patch_meeting(mid, title=new_title, status=new_status, tags=new_tags)
                st.toast("Saved ✅")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Save failed: {e}")

        st.markdown("---")

        # --- uploads ---------------------------------------------------------
        upl = st.file_uploader("Upload slides (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=True, key=f"upl-{mid}")
        cols = st.columns(3)
        if upl and cols[0].button("Upload", key=f"upbtn-{mid}"):
            try:
                res = upload_slides(mid, upl)
                saved = res.get("saved") or res.get("uploaded") or []
                st.success(f"Uploaded: {', '.join(saved) if saved else '(ok)'}")
            except Exception as e:
                st.error(f"Upload failed: {e}")

        # start processing job + poll logs
        if cols[1].button("Process meeting", key=f"proc-{mid}"):
            try:
                jid = start_job_process_meeting(mid)
                st.session_state[f"job-{mid}"] = jid
                st.toast(f"Job #{jid} started")
            except Exception as e:
                st.error(f"Failed to start job: {e}")

        # zip download
        if cols[2].button("Download slides.zip", key=f"zipbtn-{mid}"):
            content = download_zip(mid)
            if content:
                st.download_button("Save ZIP", data=content, file_name=f"meeting-{mid}-slides.zip", mime="application/zip")
            else:
                st.warning("No slides uploaded yet or ZIP not available.")

        # live job polling (if any)
        jid = st.session_state.get(f"job-{mid}")
        if jid:
            if hasattr(st, "status"):
                with st.status(f"Polling job #{jid}…", expanded=False) as s:
                    logs = ""
                    for _ in range(30):
                        try:
                            jr = get_job(jid)
                            logs = get_job_logs(jid)
                            s.update(label=f"Job #{jid}: {jr.get('status','?')}")
                            if jr.get("status") in ("done", "failed"):
                                break
                            time.sleep(0.5)
                        except Exception as e:
                            st.error(f"Polling error: {e}")
                            break
                    st.code(logs or "(no logs)")
                    s.update(state="complete")
            else:
                st.info(f"Job #{jid} running…")

        # --- preview existing files -----------------------------------------
        files = []
        try:
            files = list_files(mid)
        except Exception:
            pass

        if files:
            st.write("**Files:**", ", ".join(files))
            for fn in files:
                try:
                    r = requests.get(f"{API}/meetings/{mid}/slides/{fn}", headers=HEADERS, timeout=30)
                    if r.status_code != 200:
                        continue
                    if fn.lower().endswith(".txt"):
                        st.subheader(fn)
                        st.code(r.text, language="text")
                    elif fn.lower().endswith(".pdf"):
                        st.subheader(fn)
                        embed_pdf(r.content, height=420)
                except Exception:
                    continue
        else:
            st.caption("No files yet.")

