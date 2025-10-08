# frontend/frontend_api.py
from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", st.secrets.get("API_BASE", "http://127.0.0.1:8000"))
API_KEY = st.secrets.get("API_KEY", os.getenv("API_KEY", "dev-secret-123"))
DEFAULT_HEADERS: dict[str, str] = {"X-API-Key": API_KEY}


def _full(path: str) -> str:
    """Return an absolute URL for the API, accepting either absolute or relative paths."""
    if path.startswith(("http://", "https://")):
        return path
    return f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"


def get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    **kwargs: Any,
) -> requests.Response:
    """GET wrapper that injects default headers and timeout."""
    hdrs = {**DEFAULT_HEADERS, **(headers or {})}
    return requests.get(_full(url), headers=hdrs, timeout=timeout, **kwargs)


def post(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    **kwargs: Any,
) -> requests.Response:
    """POST wrapper that injects default headers and timeout."""
    hdrs = {**DEFAULT_HEADERS, **(headers or {})}
    return requests.post(_full(url), headers=hdrs, timeout=timeout, **kwargs)


def get_json(url: str, **kwargs: Any) -> Any:
    """GET and return JSON, raising for HTTP errors."""
    r = get(url, **kwargs)
    r.raise_for_status()
    return r.json()

