# frontend/frontend_api.py
import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

def _full(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return API_BASE.rstrip("/") + "/" + url.lstrip("/")

def api_get(path: str, **kwargs):
    try:
        r = requests.get(_full(path), timeout=20, **kwargs)
        if r.status_code >= 400:
            try:
                err = r.json()
            except Exception:
                err = {"error": "HTTPError", "message": r.text, "details": None}
            raise RuntimeError(err.get("message", "Request failed"), err)
        return r.json()
    except Exception as e:
        # Extract standardized error if passed via RuntimeError
        details = None
        msg = str(e)
        if isinstance(e, RuntimeError) and len(e.args) > 1 and isinstance(e.args[1], dict):
            details = e.args[1]
        _show_error_banner("Request failed", msg, details)
        return None

def _show_error_banner(title: str, message: str, details: dict | None = None):
    with st.container(border=True):
        st.error(f"**{title}** — {message}")
        if details:
            with st.expander("Details"):
                st.json(details, expanded=False)

