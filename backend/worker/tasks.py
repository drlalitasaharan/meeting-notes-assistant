import importlib
import inspect
import json
import pkgutil
import time

import app.jobs as jobs_pkg
from app.storage import choose_storage

# Hoist functions from app.jobs.*
for mi in pkgutil.walk_packages(jobs_pkg.__path__, jobs_pkg.__name__ + "."):
    mod = importlib.import_module(mi.name)
    for name, obj in vars(mod).items():
        if inspect.isfunction(obj):
            globals()[name] = obj


def _put_json(storage, key, data):
    body = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    # Try common storage methods
    for name in ("write", "put", "upload", "save"):
        if hasattr(storage, name):
            try:
                getattr(storage, name)(key, body)
                break
            except Exception:
                pass
    else:
        # Fallback: boto3-style client if exposed
        try:
            client = getattr(storage, "client", None)
            bucket = getattr(storage, "bucket", None) or getattr(storage, "bucket_name", None)
            if client and bucket:
                client.put_object(Bucket=bucket, Key=key, Body=body, ContentType="application/json")
        except Exception:
            pass
    try:
        return storage.sign_url(key)
    except Exception:
        return key


def demo_job(payload=None, job_id=None, **kwargs):
    """Accepts API kwarg 'job_id' and returns a signed URL to a JSON artifact."""
    storage = choose_storage()
    ts = int(time.time())
    key = f"jobs/demo-{job_id or ts}.json"
    doc = {"ok": True, "ts": ts, "job_id": job_id, "payload": payload}
    return _put_json(storage, key, doc)
