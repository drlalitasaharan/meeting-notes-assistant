import base64
import time
import os
from typing import List, Dict, Any

import requests
import streamlit as st

# ---------------------------------------------------------------------
# Config (prefer Streamlit secrets, then env, then sensible defaults)
# ---------------------------------------------------------------------
API: str = (
    st.secrets.get("API_BASE")
    or os.getenv("API_BASE")
    or "http://api:8000/v1"  # use docker service name by default
)
API_KEY: str = (
    st.secrets.get("X_API_KEY")
    or st.secrets.get("API_KEY")
    or os.getenv("X_API_KEY")
    or os.getenv("API_KEY", "dev-secret-123")
)
HEADERS = {"X-API-Key": API_KEY}
TIMEOUT = 10

st.set_page_config(page_title="Meeting Notes Assistant", layout="wide")
st.title("Meeting Notes Assistant")

# --- quick create ------------------------------------------------------
with st.form("new-meeting"):
    c1, c2 = st.columns([3, 2])
    title = c1.text_input("Title")
    tags = c2.text_input("Tags (comma-separated)")
    create = st.form_submit_button("Create")
    if create:
        r = requests.post(
            f"{API}/meetings",
            headers=HEADERS,
            params={"title": title, "tags": tags},
            timeout=TIMEOUT,
        )
        st.toast("Created!" if r.ok else f"Failed: {r.status_code}", icon="✅" if r.ok else "❌")
        st.rerun()

# --- helpers -----------------------------------------------------------
def status_chip(s: str) -> str:
    colors = {
        "new": "gray",
        "processing": "orange",
        "done": "green",
        "failed": "red",
        "queued": "blue",
        "running": "orange",
    }
    return (
        f"<span style='padding:2px 8px;border-radius:12px;"
        f"background:{colors.get(s, 'gray')};color:white;font-size:12px'>{s}</span>"
    )

def embed_pdf(b: bytes, height: int = 450):
    b64 = base64.b64encode(b).decode()
    st.components.v1.html(
        f"""
        <embed src="data:application/pdf;base64,{b64}"
               type="application/pdf" width="100%" height="{height}px" />
        """,
        height=height + 12,
    )

def list_meetings(query: str = "", tag: str = "") -> List[Dict[str, Any]]:
    r = requests.get(
        f"{API}/meetings",
        params={"query": query or None, "tag": tag or None, "page": 1, "limit": 50},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("items", []) if isinstance(data, dict) else []

def list_files(mid: int) -> List[str]:
    """Return filenames for a meeting as a list of strings.

    Handles API shapes:
      - {"items": [...]} or {"files": [...]}
      - [...]  (list of strings or list of dicts with 'filename')
    """
    try:
        r = requests.get(f"{API}/meetings/{mid}/slides", headers=HEADERS, timeout=TIMEOUT)
    except Exception:
        return []
    if not r.ok:
        return []

    try:
        data = r.json()
    except ValueError:
        return []

    # extract the list payload
    if isinstance(data, dict):
        payload = data.get("items") or data.get("files") or []
    else:
        payload = data

    # normalize to list[str]
    filenames: List[str] = []
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, str):
                filenames.append(item)
            elif isinstance(item, dict):
                name = item.get("filename") or item.get("name") or item.get("key")
                if isinstance(name, str):
                    filenames.append(name)

    return filenames

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
    st.caption(f"{len(items)} meeting(s) found")
with c2:
    if st.button("Clear filters"):
        st.session_state.clear()
        st.rerun()

# --- list --------------------------------------------------------------
for m in items:
    with st.expander(f"#{m['id']} · {m['title']}"):
        st.markdown(f"**Status:** {status_chip(m['status'])}", unsafe_allow_html=True)
        st.write("**Tags:**", ", ".join(m.get("tags", [])) or "—")

        upl = st.file_uploader(
            "Upload slides (PDF/TXT)",
            type=["pdf", "txt"],
            accept_multiple_files=True,
            key=f"upl-{m['id']}",
        )
        cols = st.columns(3)
        if upl and cols[0].button("Upload", key=f"upbtn-{m['id']}"):
            tosend = [("files", (f.name, f.getvalue())) for f in upl]
            r = requests.post(
                f"{API}/meetings/{m['id']}/slides",
                headers=HEADERS,
                files=tosend,
                timeout=TIMEOUT,
            )
            if r.ok:
                saved = (
                    r.json().get("saved", [])
                    if r.headers.get("content-type", "").startswith("application/json")
                    else []
                )
                msg = f"Uploaded: {', '.join(saved)}" if saved else "Uploaded."
                st.success(msg)
            else:
                st.error(f"Upload failed: {r.status_code}")

        if cols[1].button("Process meeting", key=f"proc-{m['id']}"):
            r = requests.post(
                f"{API}/jobs",
                params={"type": "process_meeting", "meeting_id": m["id"]},
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            if r.ok:
                st.session_state[f"job-{m['id']}"] = r.json()["id"]
            else:
                st.error("Failed to start job")

        if cols[2].button("Download slides.zip", key=f"zip-{m['id']}"):
            r = requests.get(
                f"{API}/meetings/{m['id']}/slides.zip",
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            if r.status_code == 200:
                st.download_button(
                    "Save ZIP",
                    data=r.content,
                    file_name=f"meeting-{m['id']}-slides.zip",
                    mime="application/zip",
                )
            else:
                st.warning("No slides uploaded yet.")

        # live job polling (if any)
        jid = st.session_state.get(f"job-{m['id']}")
        if jid:
            with st.status(f"Polling job #{jid}…", expanded=False) as s:
                for _ in range(24):
                    jr = requests.get(f"{API}/jobs/{jid}", headers=HEADERS, timeout=TIMEOUT).json()
                    logs_resp = requests.get(
                        f"{API}/jobs/{jid}/logs", headers=HEADERS, timeout=TIMEOUT
                    )
                    logs = logs_resp.text
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
                r = requests.get(
                    f"{API}/meetings/{m['id']}/slides/{fn}",
                    headers=HEADERS,
                    timeout=TIMEOUT,
                )
                if r.status_code != 200:
                    continue
                if fn.lower().endswith(".txt"):
                    st.subheader(fn)
                    st.code(r.text, language="text")
                elif fn.lower().endswith(".pdf"):
                    st.subheader(fn)
                    embed_pdf(r.content, height=420)
        else:
            st.warning("No slides uploaded yet.")

