# backend/packages/shared/schemas.py
from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Short error identifier")
    message: str = Field(..., description="Human-readable message")
    details: Any | None = Field(None, description="Optional extra info")
