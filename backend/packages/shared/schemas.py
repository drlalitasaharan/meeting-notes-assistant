from pydantic import BaseModel, Field
from typing import Any, Optional

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Short error identifier")
    message: str = Field(..., description="Human-readable message")
    details: Optional[Any] = Field(None, description="Optional extra info")

