# frontend/streamlit_app.py
"""
Streamlit app for Meeting Notes Assistant (MVP).

Includes:
  • Robust error handling, retry logic, and a tuning panel.
  • Phase-1 polish:
      - Environment banner (Demo/Prod/Dev)
      - Meeting list with 📎 slides indicator and one-click ⬇️ download
      - Quick actions (start meeting & attach slides)
      - Clean labels and compact card view
  • Overlap fixes:
      - Global CSS for line-height, nowrap buttons, badge layout, and ID wrapping
      - Widened column ratios to avoid cramped controls
      - Shorter labels (“Auto-refresh”)
  • Debug panel (opt-in) with request timings.
"""

import os
import io
import time
import json
from typing import Any, Dict, Optional, List

import requests
import streamlit as st
from dotenv import load_dotenv
from requests.exceptions import Timeout, ConnectionError as ReqConnectionError

# --------------------------------------------------
# Configuration
load_dotenv()
API_BASE = (os.getenv("API_BASE_URL") or "http://127.0.0.1:8000/v1").rstrip("/")
APP_ENV = (os.getenv("APP_ENV") or "dev").lower()  # 'dev' | 'demo' | 'prod'
# Auto-fill a fake token in DEMO unless explicitly provided via env
DEFAULT_AUTH = (os.getenv("AUTH_BEARER") or ("demo-token" if APP_ENV == "demo" else "")).strip()

st.set_page_config(page_title="Meeting Notes Assistant — MVP", layout="wide")
st.title("📝 Meeting Notes Assistant — MVP Test UI")
st.caption("Configure API in the sidebar if needed.")

# ✅ Environment banner
_env_color = {"prod": "#0b7a0b", "demo": "#cc7a00", "dev": "#444"}.get(APP_ENV, "#444")
st.markdown(
    f"""
    <div style="padding:8px 12px;border-radius:8px;background:{_env_color};color:white;margin:8px 0 16px 0;">
      <b>Environment:</b> {APP_ENV.upper()}
    </div>
    """,
    unsafe_allow_html=True,
)

# -------- Overlap / layout CSS fixes --------
st.markdown(
    """
    <style>
      /* general typography spacing */
      .stMarkdown, .stText, .stCaption, .stMetric { line-height: 1.35; }

      /* prevent short button labels from wrapping; give emojis breathing room */
      .stButton > button { white-space: nowrap; line-height: 1.2; padding: 0.4rem 0.9rem; }

      /* badge layout (inline-flex keeps icons & text aligned) */
      .badge { display: inline-flex; align-items: center; line-height: 1; }

      /* long IDs/URLs wrap nicely without pushing layout */
      code, .meeting-id {
        word-break: break-all;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      }

      /* card spacing */
      .card { display:block; margin-bottom: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Session state
for key, val in {
    "api_base": API_BASE,
    "auth": DEFAULT_AUTH,
    "meeting_id": "",
    "meeting": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

if "cfg" not in st.session_state:
    st.session_state.cfg = {
        "get_timeout": 30,
        "post_timeout": 60,
        "upload_timeout": 120,
        "retries": 2,
        "base_delay": 0.5,
        "poll_seconds": 30,
        "max_mb": 50,
    }

if "debug_logs" not in st.session_state:
    st.session_state.debug_logs = []


# --------------------------------------------------
# Utility functions

def _headers() -> Dict[str, str]:
    h = {"accept": "application/json"}
    if st.session_state.auth:
        h["Authorization"] = f"Bearer {st.session_state.auth}"
    return h


def _handle_response(resp: requests.Response) -> Any:
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text[:1200]}
    if not resp.ok:
        err_msg = None
        if isinstance(data, dict):
            err_msg = data.get("error") or data.get("detail") or data.get("message")
        err_msg = err_msg or f"HTTP {resp.status_code}"
        raise RuntimeError(json.dumps({"message": err_msg, "status": resp.status_code, "body": data}))
    return data


def _fmt_error(e: Exception) -> str:
    try:
        payload = json.loads(str(e))
        msg = payload.get("message", "Request failed")
        status = payload.get("status")
        return f"{msg}{f' (HTTP {status})' if status else ''}"
    except Exception:
        if isinstance(e, (ReqConnectionError, Timeout)):
            return f"Network error: {e.__class__.__name__} — check **API Base URL** in the sidebar."
        return f"{e.__class__.__name__}: {str(e)[:600]}"


import time as _time
def _retry(fn, *args, retries=None, base_delay=None, **kwargs):
    retries = retries if retries is not None else st.session_state.cfg["retries"]
    base_delay = base_delay if base_delay is not None else st.session_state.cfg["base_delay"]
    last = None
    for i in range(retries + 1):
        try:
            return fn(*args, **kwargs)
        except (ReqConnectionError, Timeout) as e:
            last = e
            _time.sleep(base_delay * (2 ** i))
        except RuntimeError as e:
            try:
                if json.loads(str(e)).get("status") in (502, 503, 504):
                    last = e
                    _time.sleep(base_delay * (2 ** i))
                    continue
            except Exception:
                pass
            raise
    raise last if last else RuntimeError("Request failed after retries")


def _join(*parts: str) -> str:
    parts = [p.strip("/") for p in parts if p]
    return "/".join([parts[0]] + parts[1:]) if parts else ""


def _api_root_from_base() -> str:
    base = st.session_state.api_base.rstrip("/")
    return base[:-3] if base.endswith("/v1") else base


def _safe_preview(body: Any, limit: int = 400) -> str:
    try:
        return json.dumps(body, indent=2)[:limit] if isinstance(body, (dict, list)) else str(body)[:limit]
    except Exception:
        return "<unpreviewable>"


def _log_debug(method: str, path: str, latency_ms: int, status=None, body=None, note=""):
    st.session_state.debug_logs.insert(0, {
        "method": method, "path": path, "latency_ms": latency_ms,
        "status": status, "preview": _safe_preview(body), "note": note,
        "ts": time.strftime("%H:%M:%S"),
    })
    st.session_state.debug_logs = st.session_state.debug_logs[:10]


class Timed:
    def __enter__(self): self.t0 = time.perf_counter(); return self
    def __exit__(self, *exc): self.ms = int((time.perf_counter() - self.t0) * 1000)


# -----------------------------------------------------------------------------
# Toast helper
def _toast(msg: str, kind="info"):
    if hasattr(st, "toast"):
        st.toast(f"❌ {msg}" if kind == "error" else msg); return
    getattr(st, kind if kind in {"success", "error", "warning"} else "info")(msg)


TERMINAL_STATES = {"done", "completed", "finished", "error", "failed"}

def poll_meeting(getter, meeting_id: str, seconds=None, min_interval: float = 1.5, max_interval: float = 6.0):
    seconds = seconds if seconds is not None else st.session_state.cfg["poll_seconds"]
    start = time.time()
    attempt = 0
    interval = max(0.5, min_interval)
    while True:
        attempt += 1
        payload = _retry(lambda: getter(meeting_id))
        yield attempt, payload
        status = str(payload.get("status", "")).lower()
        if status in TERMINAL_STATES:
            break
        if time.time() - start > seconds:
            break
        time.sleep(interval)
        interval = min(max_interval, interval * 1.6)


# -----------------------------------------------------------------------------
# API wrappers
def api_start_meeting(name: str):
    for path in ("meetings/start", "start"):
        try:
            return _handle_response(requests.post(
                _join(st.session_state.api_base, path),
                json={"name": name}, headers=_headers(),
                timeout=st.session_state.cfg["post_timeout"],
            ))
        except Exception:
            continue
    raise RuntimeError("Could not reach start endpoint")


def api_list_meetings():
    resp = requests.get(
        _join(st.session_state.api_base, "meetings"),
        headers=_headers(), timeout=st.session_state.cfg["get_timeout"],
    )
    return _handle_response(resp)


def api_get_meeting(meeting_id: str):
    resp = requests.get(
        _join(st.session_state.api_base, f"meetings/{meeting_id}"),
        headers=_headers(), timeout=st.session_state.cfg["get_timeout"],
    )
    return _handle_response(resp)


def api_attach_slides(meeting_id: str, file_bytes: bytes, filename: str):
    url = _join(st.session_state.api_base, f"meetings/{meeting_id}/attach-slides")
    resp = requests.post(url, files={"file": (filename, io.BytesIO(file_bytes))},
                         headers=_headers(), timeout=st.session_state.cfg["upload_timeout"])
    return _handle_response(resp)


def api_process_meeting(meeting_id: str):
    resp = requests.post(
        _join(st.session_state.api_base, f"meetings/{meeting_id}/process"),
        headers=_headers(), timeout=st.session_state.cfg["post_timeout"],
    )
    return _handle_response(resp)


def api_download_slides_url(meeting_id: str) -> Optional[str]:
    """
    Phase-1 helper endpoint returns {"url": "<presigned>", "expires_in": 3600}
    """
    try:
        resp = requests.get(
            _join(st.session_state.api_base, f"meetings/{meeting_id}/download/slides"),
            headers=_headers(), timeout=st.session_state.cfg["get_timeout"],
        )
        return _handle_response(resp).get("url")
    except Exception:
        return None


# -----------------------------------------------------------------------------
# Compact meeting cards
def _badge(text: str) -> str:
    return (
        "<span class='badge' style='padding:2px 8px;margin-right:6px;border-radius:999px;"
        "font-size:12px;background:#eef2ff;color:#3730a3;border:1px solid #c7d2fe;'>"
        f"{text}</span>"
    )

def render_meeting_card(m: Dict[str, Any]) -> None:
    mid = m.get("meetingId") or m.get("meeting_id") or m.get("id") or ""
    title = m.get("name") or m.get("title") or "(no name)"
    created = (m.get("created_at") or "")[:19].replace("T", " ")
    slides_attached = bool(m.get("slides_attached"))
    transcript_available = bool(m.get("transcript_available"))

    st.markdown(
        f"""
        <div class="card" style="padding:12px 14px;border:1px solid #e5e7eb;border-radius:12px;">
          <div style="font-weight:600;font-size:16px;">{title}</div>
          <div style="color:#6b7280;font-size:12px;">{created} · <span class="meeting-id">{mid}</span></div>
          <div style="margin:6px 0;">
            { _badge("📎 slides attached") if slides_attached else _badge("— no slides —") }
            { _badge("🗒️ transcript") if transcript_available else "" }
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Wider "Use" button column to avoid wrapping + full-width buttons
    c1, c2 = st.columns([4, 6])
    with c1:
        if st.button("✅ Use", key=f"use_{mid}", use_container_width=True):
            st.session_state.meeting_id = mid
            _toast("Selected meeting")
    with c2:
        if slides_attached:
            url = api_download_slides_url(mid)
            if url:
                st.link_button("⬇️ Download slides", url, use_container_width=True)


# -----------------------------------------------------------------------------
# Sidebar
with st.sidebar:
    st.subheader("⚙️ Settings")
    st.text_input("API Base URL", key="api_base")
    st.text_input("Auth Bearer (optional)", key="auth", type="password")
    if st.session_state.get("auth"):
        st.caption("Authorization header will be sent (Bearer ****).")
    else:
        st.caption("No Authorization header will be sent.")
    st.caption(f"Environment: **{APP_ENV}**")

    with st.expander("🧪 Tuning"):
        c = st.session_state.cfg
        c["get_timeout"] = st.number_input("GET timeout (sec)", 5, 300, c["get_timeout"])
        c["post_timeout"] = st.number_input("POST timeout (sec)", 10, 600, c["post_timeout"])
        c["upload_timeout"] = st.number_input("Upload timeout (sec)", 30, 600, c["upload_timeout"])
        c["retries"] = st.number_input("Retry attempts", 0, 10, c["retries"])
        c["base_delay"] = st.number_input("Retry base delay (sec)", 0.1, 10.0, float(c["base_delay"]))
        c["poll_seconds"] = st.number_input("Poll total budget (sec)", 10, 600, c["poll_seconds"])
        c["max_mb"] = st.number_input("Upload max size (MB)", 1, 1024, c["max_mb"])

    debug_mode = st.checkbox("🪵 Debug mode", value=False if APP_ENV == "prod" else False)
    if st.button("🔁 Refresh meetings list"):
        st.session_state["_force_refresh_list"] = True

# Reachability check
try:
    _ = _retry(lambda: requests.get(_join(_api_root_from_base(), "openapi.json"), timeout=5))
except Exception:
    st.warning("Backend may be unreachable. Verify API Base URL.")

# -----------------------------------------------------------------------------
# Main layout
colA, colB = st.columns([1, 2], gap="large")

# === Column A: Create / Select ===
with colA:
    st.header("1) Create / Select")

    # Quick actions: Start meeting
    with st.form("start_form", clear_on_submit=True):
        name = st.text_input("Meeting name", placeholder="e.g., Project Kickoff")
        if st.form_submit_button("➕ Create meeting"):
            try:
                data = _retry(lambda: api_start_meeting(name or "Untitled"))
                _toast("Meeting created", "success")
                st.session_state.meeting_id = (
                    data.get("meetingId") or data.get("meeting_id") or data.get("id") or ""
                )
                st.session_state.meeting = data
            except Exception as e:
                st.error(_fmt_error(e))

    # Meeting list with 📎 indicator
    meetings_list: List[Dict[str, Any]] = []
    try:
        lst = _retry(api_list_meetings)
        meetings_list = lst.get("items") or lst
    except Exception as e:
        st.error(_fmt_error(e))

    # Selector with indicators
    ids, labels = [], []
    for m in meetings_list or []:
        mid = m.get("meetingId") or m.get("meeting_id") or m.get("id")
        nm = m.get("name") or m.get("title") or "(no name)"
        created = (m.get("created_at") or "")[:19].replace("T", " ")
        pin = " 📎" if m.get("slides_attached") else ""
        note = " 🗒️" if m.get("transcript_available") else ""
        if mid:
            ids.append(mid)
            labels.append(f"{nm}{pin}{note} · {mid}{f' · {created}' if created else ''}")

    if ids:
        sel = st.selectbox("Select meeting", options=list(range(len(ids))), format_func=lambda i: labels[i], index=0)
        if st.button("✅ Use selected"):
            st.session_state.meeting_id = ids[sel]

    st.markdown("### Compact view")
    if meetings_list:
        for m in meetings_list:
            render_meeting_card(m)
    else:
        st.caption("No meetings yet.")

    st.info(f"Active Meeting ID: **{st.session_state.meeting_id or '—'}**")


# === Column B: Upload → Process → Results ===
with colB:
    st.header("2) Slides → Process → Results")
    if not st.session_state.meeting_id:
        st.warning("Create or select a meeting first.")
    else:
        # Quick actions: Attach slides
        st.subheader("Upload slides")
        up = st.file_uploader("Choose a file (PDF, PPTX, or TXT for testing)", accept_multiple_files=False)
        # Wider ratios reduce wrapping
        c1, c2, c3 = st.columns([1.1, 1.3, 1.6])

        with c1:
            if st.button("📎 Attach to meeting", disabled=up is None):
                if not up:
                    st.error("Choose a file first.")
                else:
                    max_mb = st.session_state.cfg["max_mb"]
                    if getattr(up, "size", 0) > max_mb * 1024 * 1024:
                        st.error(f"File too large (> {max_mb} MB).")
                    else:
                        try:
                            with Timed() as t:
                                _ = _retry(lambda: api_attach_slides(st.session_state.meeting_id, up.read(), up.name))
                            _toast("Slides attached", "success")
                            _log_debug("POST", f"/meetings/{{id}}/attach-slides", t.ms, status=200, body={"filename": up.name})
                            with Timed() as t2:
                                st.session_state.meeting = _retry(lambda: api_get_meeting(st.session_state.meeting_id))
                            _log_debug("GET", f"/meetings/{{id}}", t2.ms, status=200)
                        except Exception as e:
                            st.error(_fmt_error(e))

        with c2:
            presigned = api_download_slides_url(st.session_state.meeting_id)
            if presigned:
                st.caption("Presigned download:")
                st.markdown(f"[⬇️ Download attached slides]({presigned})")
            else:
                st.caption("No presigned slide URL (yet).")

        with c3:
            # Optional: list of slide links if your API provides /meetings/{id}/slides
            try:
                lst_url = _join(st.session_state.api_base, f"meetings/{st.session_state.meeting_id}/slides")
                resp = _retry(lambda: requests.get(lst_url, headers=_headers(), timeout=st.session_state.cfg["get_timeout"]))
                files = _handle_response(resp)
                if files:
                    st.caption("All slide links")
                    for f in files:
                        if f.get("url"):
                            st.markdown(f"- [⬇️ {f.get('filename')}]({f.get('url')})")
                        else:
                            st.write(f"- {f.get('filename')} (no URL)")
                else:
                    st.caption("No slides found.")
            except Exception:
                pass

        st.markdown("---")

        # Process meeting
        st.subheader("Process meeting")
        # Widen ratios to avoid label wrapping; shorten label text
        p1, p2, p3 = st.columns([1.2, 1.2, 1.6])

        with p1:
            if st.button("⚙️ Start processing"):
                try:
                    with Timed() as t:
                        res = _retry(lambda: api_process_meeting(st.session_state.meeting_id))
                    _toast("Processing started", "success")
                    _log_debug("POST", f"/meetings/{{id}}/process", t.ms, status=200, body=res)
                except Exception as e:
                    st.error(_fmt_error(e))

        with p2:
            autorefresh = st.checkbox("Auto-refresh", value=False)
            refresh_secs = st.number_input("Every (sec)", value=3, min_value=1, max_value=30)

        with p3:
            if st.button("🔄 Refresh meeting data"):
                try:
                    with Timed() as t:
                        st.session_state.meeting = _retry(lambda: api_get_meeting(st.session_state.meeting_id))
                    st.success("Updated.")
                    _log_debug("GET", f"/meetings/{{id}}", t.ms, status=200)
                except Exception as e:
                    st.error(_fmt_error(e))

        if autorefresh:
            if hasattr(st, "status"):
                with st.status("Auto-refreshing…", expanded=True) as status_box:
                    try:
                        for i, m in poll_meeting(
                            api_get_meeting,
                            st.session_state.meeting_id,
                            seconds=st.session_state.cfg["poll_seconds"],
                            min_interval=float(refresh_secs),
                            max_interval=float(refresh_secs) * 2.0,
                        ):
                            st.session_state.meeting = m
                            st.write(f"Attempt {i}: status = **{m.get('status','unknown')}**")
                            final = str(m.get("status", "")).lower()
                            if final in TERMINAL_STATES:
                                status_box.update(label="Processing finished", state="complete")
                                _toast(
                                    "Processing finished" if final in {"done","completed","finished"} else "Processing failed",
                                    "success" if final in {"done","completed","finished"} else "error"
                                )
                                break
                        else:
                            status_box.update(label="Stopped polling (time budget reached)", state="complete")
                    except Exception as e:
                        status_box.update(label="Auto-refresh error", state="error")
                        st.error(_fmt_error(e))
            else:
                info_placeholder = st.empty()
                log_placeholder = st.empty()
                info_placeholder.info("Auto-refreshing…")
                try:
                    for i, m in poll_meeting(
                        api_get_meeting,
                        st.session_state.meeting_id,
                        seconds=st.session_state.cfg["poll_seconds"],
                        min_interval=float(refresh_secs),
                        max_interval=float(refresh_secs) * 2.0,
                    ):
                        st.session_state.meeting = m
                        log_placeholder.write(f"Attempt {i}: status = **{m.get('status','unknown')}**")
                        final = str(m.get("status", "")).lower()
                        if final in TERMINAL_STATES:
                            info_placeholder.info("Processing finished")
                            _toast(
                                "Processing finished" if final in {"done","completed","finished"} else "Processing failed",
                                "success" if final in {"done","completed","finished"} else "error"
                            )
                            break
                    else:
                        info_placeholder.info("Stopped polling (time budget reached)")
                except Exception as e:
                    info_placeholder.error("Auto-refresh error")
                    st.error(_fmt_error(e))

        st.markdown("---")

        # Results
        st.subheader("Results")
        meeting = st.session_state.meeting
        if meeting is None:
            try:
                with Timed() as t:
                    meeting = _retry(lambda: api_get_meeting(st.session_state.meeting_id))
                st.session_state.meeting = meeting
                _log_debug("GET", f"/meetings/{{id}}", t.ms, status=200)
            except Exception as e:
                st.info(_fmt_error(e))

        if meeting:
            a, b, c = st.columns([1.1, 0.9, 1.0])
            a.metric("Status", meeting.get("status", "unknown") or "—")
            slides_val = meeting.get("slides", [])
            b.metric("Slides", str(len(slides_val) if isinstance(slides_val, list) else 0))
            c.metric("Created", (meeting.get("created_at") or "")[:19].replace("T", " "))

            tabs = st.tabs(["🗒️ Transcript", "🧾 Summary", "🧩 Raw JSON"])
            with tabs[0]:
                ttxt = meeting.get("transcript")
                if isinstance(ttxt, dict):
                    ttxt = ttxt.get("text")
                st.text_area("Transcript", ttxt or "— No transcript yet —", height=300)
            with tabs[1]:
                s = meeting.get("summary")
                if isinstance(s, dict):
                    s = s.get("raw") or s.get("raw_md") or json.dumps(s, indent=2)
                st.markdown(s or "_No summary yet._")
            with tabs[2]:
                st.code(json.dumps(meeting, indent=2))
        else:
            st.info("Meeting data not available yet. Use Refresh after processing completes.")

# --------------------------------------------------
# Debug expander
if 'debug_mode' in locals() and debug_mode:
    with st.expander("🔧 Debug / recent requests"):
        if not st.session_state.debug_logs:
            st.write("_No requests logged yet._")
        else:
            for row in st.session_state.debug_logs:
                line = f"[{row['ts']}] {row['method']} {row['path']} — "
                line += f"{(str(row['status']) if row['status'] is not None else '—')} — {row['latency_ms']} ms"
                if row.get("note"):
                    line += f" — {row['note']}"
                st.write(line)
                if row["preview"]:
                    st.code(row["preview"])

