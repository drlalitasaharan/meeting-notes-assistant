import time
from typing import Any, Dict


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = str(payload.get("text", ""))
    delay = float(payload.get("delay", 0))
    if delay > 0:
        time.sleep(delay)
    return {"echo": text, "length": len(text)}
