from datetime import datetime
from typing import Any

class Meeting:
    id: Any
    title: Any
    tags: Any
    status: Any
    created_at: datetime
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
