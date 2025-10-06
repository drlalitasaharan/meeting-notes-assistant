# frontend/streamlit_app.py
from __future__ import annotations

import base64
from contextlib import suppress
from typing import Any, Iterable

import requests
import streamlit as st

# ---------------------------
# Config
# ---------------------------
API = st.secrets.get("API_BASE", "http://127.0.0.1:8000/v1")
API_KEY = st.secrets.get("API_KEY", "dev-secret-123")
HEADERS = {"X-API-Key": API_KEY}
TIMEOUT = 30


# ---------------------------
# API helpers
# ---------------------------
def create_meeting(title: str, tags: str) -> dict[str, Any]:
    r = requests.post(
        f"{API}/meetings",
        params={"title": title, "tags": tags or ""},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def patch_meeting(
    mid: int, *, title: str | None = None, status: str | None = None, tags: str | None = None
) -> dict[str, Any]:
    r = requests.patch(
        f"{API}/meetings/{mid}",
        params={"title": title, "status": status, "tags": tags},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def list_files(mid: int) -> list[str]:
    r = requests.get(f"{API}/meetings/{mid}/slides", headers=HEADERS, timeout=TIMEOUT)
    if r.status_code == 200:
        js = r.json()
        if isinstance(js, list):
            return js
        if isinstance(js, dict):
            # support {"items":[{"filename":"a"}, ...]} or {"files":[...]}
            if "items" in js:
                return [it.get("filename") for it in js["items"] if "filename" in it]
            if "files" in js and isinstance(js["files"], list):
                return [str(x) for x in js["files"]]
    return []


def upload_slides(mid: int, files: Iterable[Any]) -> dict[str, Any]:
    tosend = [("files", (f.name, f.getvalue())) for f in files]
    r = requests.post(
        f"{API}/meetings/{mid}/slides",
        headers=HEADERS,
        files=tosend,
        timeout=max(TIMEOUT, 120),
    )
    r.raise_for_status()
    return r.json()


def download_zip(mid: int) -> bytes | None:
    r = requests.get(f"{API}/meetings/{mid}/slides.zip", headers=HEADERS, timeout=60)
    return r.content if r.status_code == 200 else None


def fetch_file(mid: int, filename: str) -> requests.Response | None:
    try:
        r = requests.get(
            f"{API}/meetings/{mid}/slides/{filename}",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        return r if r.status_code == 200 else None
    except Exception:
        return None


def delete_file(mid: int, filename: str) -> bool:
    r = requests.delete(
        f"{API}/meetings/{mid}/slides/{filename}",
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    return r.status_code in (200, 204)


def delete_meeting(mid: int) -> bool:
    r = requests.delete(f"{API}/meetings/{mid}", headers=HEADERS, timeout=TIMEOUT)
    return r.status_code in (200, 204)


# ---------------------------
# UI helpers
# ---------------------------
def _set_active_meeting(mid: int | None) -> None:
    st.session_state.meeting_id = mid


def _refresh_files(mid: int) -> None:
    with suppress(Exception):
        st.session_state.slides = list_files(mid)


def _ensure_session_state() -> None:
    if "meeting_id" not in st.session_state:
        st.session_state.meeting_id = None
    if "slides" not in st.session_state:
        st.session_state.slides = []


# ---------------------------
# App
# ---------------------------
def main() -> None:
    st.set_page_config(page_title="Meeting Notes Assistant", page_icon="📝", layout="wide")
    _ensure_session_state()

    st.title("📝 Meeting Notes Assistant")

    # ----- Create a meeting
    with st.expander("➕ Create a new meeting", expanded=st.session_state.meeting_id is None):
        with st.form("create-meeting"):
            c1, c2 = st.columns(2)
            title = c1.text_input("Title", placeholder="e.g., Sprint Planning")
            tags_in = c2.text_input("Tags (comma-separated)", placeholder="sprint, planning")
            submitted = st.form_submit_button("Create meeting", use_container_width=True)
            if submitted:
                if not title.strip():
                    st.error("Title is required.")
                else:
                    js = create_meeting(title, tags_in)
                    new_mid = int(js["id"])
                    _set_active_meeting(new_mid)
                    _refresh_files(new_mid)
                    st.success(f"Created meeting #{new_mid}")

    # ----- Meeting selector / empty state
    st.header("Manage a meeting")

    csel1, csel2, csel3 = st.columns([2, 1, 1])
    mid_input = csel1.number_input(
        "Meeting ID",
        min_value=1,
        step=1,
        value=st.session_state.meeting_id or 1,
        help="Enter an existing meeting ID or use the section above to create one.",
    )
    apply_mid = csel2.button("Activate ID", use_container_width=True)
    clear_mid = csel3.button("Clear", use_container_width=True)

    if apply_mid:
        _set_active_meeting(int(mid_input))
        _refresh_files(int(mid_input))

    if clear_mid:
        _set_active_meeting(None)
        st.session_state.slides = []

    if st.session_state.meeting_id is None:
        # Friendly empty state
        with st.container(border=True):
            st.subheader("No active meeting")
            st.write(
                "Create a meeting above or enter a Meeting ID, then click **Activate ID**. "
                "Once a meeting is active, you can upload slides, preview, download, or delete."
            )
        st.stop()

    # We have an active meeting
    mid = int(st.session_state.meeting_id)
    st.success(f"Active meeting: #{mid}")

    # ----- Actions row
    ac1, ac2, ac3, ac4 = st.columns([2, 2, 2, 2])

    # Upload
    with ac1:
        st.caption("Upload slides")
        files_u = st.file_uploader(
            "Choose files",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="slides_uploader",
        )
        upload_disabled = not files_u
        st.button(
            "⬆️ Upload",
            disabled=upload_disabled,
            use_container_width=True,
            on_click=lambda: _do_upload(mid, files_u),
        )

    # Process (kept as placeholder if your API has it)
    with ac2:
        st.caption("Process pipeline")
        can_process = len(st.session_state.slides) > 0
        st.button(
            "⚙️ Process Meeting",
            disabled=not can_process,
            use_container_width=True,
            on_click=lambda: _do_process(mid),
        )

    # Download ZIP
    with ac3:
        st.caption("Download all slides")
        st.button(
            "🗂️ Download ZIP",
            disabled=len(st.session_state.slides) == 0,
            use_container_width=True,
            on_click=lambda: _do_download_zip(mid),
        )

    # Delete meeting
    with ac4:
        st.caption("Danger zone")
        st.button(
            "🗑️ Delete Meeting",
            use_container_width=True,
            help="Removes this meeting and all its files",
            on_click=lambda: _do_delete_meeting(mid),
        )

    st.divider()

    # ----- Slides list
    st.subheader("Slides")
    if not st.session_state.slides:
        st.info("No slides uploaded yet. Upload at least one file to enable processing.")
    else:
        for fn in st.session_state.slides:
            row = st.columns([7, 1, 1])
            row[0].write(f"📄 **{fn}**")

            # Preview (image types only)
            if row[1].button("Preview", key=f"prev-{fn}"):
                resp = fetch_file(mid, fn)
                if resp is None:
                    st.warning(f"Preview unavailable for {fn}")
                else:
                    ctype = resp.headers.get("content-type", "")
                    if ctype.startswith(("image/png", "image/jpeg")):
                        st.image(resp.content, caption=fn, use_container_width=True)
                    else:
                        st.info(f"Preview supported only for images. Content-Type: {ctype or 'unknown'}")

            # Delete (per file)
            if row[2].button("Delete", key=f"del-{fn}"):
                ok = delete_file(mid, fn)
                if ok:
                    st.toast(f"Deleted {fn}")
                    _refresh_files(mid)
                else:
                    st.error(f"Failed to delete {fn}")

    # Keep the list current on initial load
    if st.session_state.slides == []:
        _refresh_files(mid)


# ---------------------------
# Action callbacks
# ---------------------------
def _do_upload(mid: int, files_u: Iterable[Any]) -> None:
    try:
        upload_slides(mid, files_u)
        st.toast("Upload complete")
    except Exception as e:
        st.error(f"Upload failed: {e}")
    finally:
        _refresh_files(mid)


def _do_process(mid: int) -> None:
    # Optional: hook up to your /meetings/{id}/process API if present.
    try:
        r = requests.post(f"{API}/meetings/{mid}/process", headers=HEADERS, timeout=max(TIMEOUT, 60))
        if r.ok:
            st.success("Processing started")
        else:
            st.error(f"Process failed: {r.text}")
    except Exception as e:
        st.error(f"Process error: {e}")


def _do_download_zip(mid: int) -> None:
    data = download_zip(mid)
    if not data:
        st.warning("No ZIP available.")
        return
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="slides_{mid}.zip">Download</a>'
    st.markdown(href, unsafe_allow_html=True)


def _do_delete_meeting(mid: int) -> None:
    if delete_meeting(mid):
        st.toast(f"Meeting #{mid} deleted")
        _set_active_meeting(None)
        st.session_state.slides = []
        st.rerun()
    else:
        st.error("Failed to delete meeting")


# ---------------------------
# Entrypoint
# ---------------------------
if __name__ == "__main__":
    main()

