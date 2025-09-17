import os
import io
import requests
import streamlit as st

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------
st.set_page_config(page_title="MNA Frontend", layout="wide")
st.title("📝 Meeting Notes Assistant — Frontend")

API_BASE = os.getenv("API_URL", "http://127.0.0.1:8000")

# Keep things in session
if "meeting" not in st.session_state:
    st.session_state.meeting = None  # {'meetingId', 'uploadUrl', 's3Key'}

# -------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------
def _require_meeting():
    if not st.session_state.meeting:
        st.warning("Start a meeting first.")
        return False
    return True


# -------------------------------------------------------------------
# Top: Health + Root
# -------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Health check")
    if st.button("Ping API"):
        try:
            r = requests.get(f"{API_BASE}/healthz", timeout=5)
            st.json(r.json())
        except Exception as e:
            st.error(f"Failed: {e}")

with col2:
    st.subheader("Root")
    try:
        r = requests.get(f"{API_BASE}/", timeout=5)
        if r.ok:
            st.json(r.json())
        else:
            st.info("Root endpoint missing (optional).")
    except Exception as e:
        st.error(f"Failed: {e}")

st.divider()

# -------------------------------------------------------------------
# 1) Start Meeting
# -------------------------------------------------------------------
st.header("1) Start Meeting")
title = st.text_input("Meeting title", "Demo Meeting")
if st.button("Start Meeting"):
    try:
        resp = requests.post(f"{API_BASE}/v1/meetings/start", data={"title": title})
        resp.raise_for_status()
        st.session_state.meeting = resp.json()
        st.success(f"Started: {st.session_state.meeting['meetingId']}")
        with st.expander("Raw response"):
            st.json(st.session_state.meeting)
    except Exception as e:
        st.error(f"Failed to start meeting: {e}")

if st.session_state.meeting:
    st.info(f"Current meeting ID: **{st.session_state.meeting['meetingId']}**")

st.divider()

# -------------------------------------------------------------------
# 2) Upload audio/blob to presigned URL (optional)
# -------------------------------------------------------------------
st.header("2) Upload Audio/Blob (optional)")
st.caption("Uploads to the presigned URL returned by /v1/meetings/start")

if st.session_state.meeting:
    upload_col1, upload_col2 = st.columns(2)

    with upload_col1:
        f_audio = st.file_uploader("Pick a file to upload to presigned URL", type=None)
        if f_audio and st.button("Upload selected file"):
            try:
                put = requests.put(
                    st.session_state.meeting["uploadUrl"],
                    data=f_audio.getvalue(),
                    headers={"Content-Length": str(len(f_audio.getvalue()))},
                    timeout=30,
                )
                st.success(f"Upload status: {put.status_code}")
            except Exception as e:
                st.error(f"Upload failed: {e}")

    with upload_col2:
        if st.button("Upload sample 'hello world'"):
            try:
                data = io.BytesIO(b"hello world")
                put = requests.put(
                    st.session_state.meeting["uploadUrl"],
                    data=data.getvalue(),
                    headers={"Content-Length": str(len(data.getvalue()))},
                    timeout=15,
                )
                st.success(f"Upload status: {put.status_code}")
            except Exception as e:
                st.error(f"Sample upload failed: {e}")
else:
    st.info("Start a meeting to get a presigned URL.")

st.divider()

# -------------------------------------------------------------------
# 3) Attach Slides (file -> POST /attach-slides)
# -------------------------------------------------------------------
st.header("3) Attach Slide(s)")
st.caption("Uploads the selected file to MinIO via the API’s /attach-slides endpoint.")

f_slide = st.file_uploader("Pick a slide/file to attach", type=None, key="slide_uploader")
if st.button("Attach slide"):
    if not _require_meeting():
        pass
    elif not f_slide:
        st.warning("Choose a file first.")
    else:
        try:
            files = {"file": (f_slide.name, f_slide.getvalue())}
            mid = st.session_state.meeting["meetingId"]
            r = requests.post(f"{API_BASE}/v1/meetings/{mid}/attach-slides", files=files, timeout=30)
            r.raise_for_status()
            st.success("Slide attached!")
            with st.expander("API response"):
                st.json(r.json())
        except Exception as e:
            st.error(f"Attach failed: {e}")

st.divider()

# -------------------------------------------------------------------
# 4) Process (demo)
# -------------------------------------------------------------------
st.header("4) Process Meeting (demo)")
if st.button("Process now"):
    if _require_meeting():
        try:
            mid = st.session_state.meeting["meetingId"]
            r = requests.post(f"{API_BASE}/v1/meetings/{mid}/process", timeout=30)
            st.json(r.json())
        except Exception as e:
            st.error(f"Process failed: {e}")

st.divider()

# -------------------------------------------------------------------
# 5) Fetch Meeting Details
# -------------------------------------------------------------------
st.header("5) Fetch Meeting Details")
if st.button("Refresh details"):
    if _require_meeting():
        try:
            mid = st.session_state.meeting["meetingId"]
            r = requests.get(f"{API_BASE}/v1/meetings/{mid}", timeout=15)
            r.raise_for_status()
            info = r.json()
            st.subheader("Meeting")
            st.json(info.get("meeting"))
            st.subheader("Transcript")
            st.json(info.get("transcript"))
            st.subheader("Summary")
            st.json(info.get("summary"))
            st.subheader("Slides")
            st.json(info.get("slides"))
        except Exception as e:
            st.error(f"Fetch failed: {e}")

st.caption("Edit me at `frontend/app.py`. Backend is at `backend/app/main.py`.")

