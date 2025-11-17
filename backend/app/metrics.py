from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

LabelDict = Mapping[str, str]
LabelKey = tuple[tuple[str, str], ...]


def _labels_key(labels: LabelDict | None) -> LabelKey:
    if not labels:
        return ()
    return tuple(sorted(labels.items()))


@dataclass
class Counter:
    name: str
    help: str
    _values: dict[LabelKey, int] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def inc(self, labels: LabelDict | None = None, value: int = 1) -> None:
        key = _labels_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) + value

    def render_prometheus(self) -> list[str]:
        lines = [f"# HELP {self.name} {self.help}", f"# TYPE {self.name} counter"]
        for key, val in self._values.items():
            label_str = ""
            if key:
                parts = [f'{k}="{v}"' for k, v in key]
                label_str = "{" + ",".join(parts) + "}"
            lines.append(f"{self.name}{label_str} {val}")
        return lines


@dataclass
class Summary:
    name: str
    help: str
    _values: dict[LabelKey, list[float]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def observe(self, value: float, labels: LabelDict | None = None) -> None:
        key = _labels_key(labels)
        with self._lock:
            self._values.setdefault(key, []).append(value)

    def render_prometheus(self) -> list[str]:
        lines = [f"# HELP {self.name} {self.help}", f"# TYPE {self.name} summary"]
        for key, samples in self._values.items():
            if not samples:
                continue
            count = len(samples)
            total = sum(samples)
            avg = total / count
            label_str = ""
            if key:
                parts = [f'{k}="{v}"' for k, v in key]
                label_str = "{" + ",".join(parts) + "}"
            lines.append(f"{self.name}_count{label_str} {count}")
            lines.append(f"{self.name}_sum{label_str} {total}")
            lines.append(f"{self.name}_avg_seconds{label_str} {avg}")
        return lines


# ---- Global metrics we care about ----

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests received by the API.",
)

HTTP_LATENCY = Summary(
    "http_request_duration_seconds",
    "Latencies for HTTP requests.",
)

JOBS_ENQUEUED = Counter(
    "jobs_enqueued_total",
    "Total jobs enqueued.",
)

JOBS_COMPLETED = Counter(
    "jobs_completed_total",
    "Total jobs completed successfully.",
)

JOBS_FAILED = Counter(
    "jobs_failed_total",
    "Total jobs that failed.",
)


@contextmanager
def track_http_request(
    path: str,
    method: str,
    status_getter: Callable[[], int],
) -> Any:
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        status = str(status_getter())
        labels = {"path": path, "method": method, "status": status}
        HTTP_REQUESTS.inc(labels)
        HTTP_LATENCY.observe(duration, labels)


def render_all_metrics_prometheus() -> str:
    """Render all metrics in a tiny Prometheus-compatible text format."""
    lines: list[str] = []
    for metric in (
        HTTP_REQUESTS,
        HTTP_LATENCY,
        JOBS_ENQUEUED,
        JOBS_COMPLETED,
        JOBS_FAILED,
    ):
        lines.extend(metric.render_prometheus())
        lines.append("")
    return "\n".join(lines).strip() + "\n"
