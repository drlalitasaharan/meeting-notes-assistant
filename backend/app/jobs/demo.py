import time


def ping(x: str) -> str:
    time.sleep(1)
    return f"pong:{x}"
