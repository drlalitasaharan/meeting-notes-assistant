from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class AuthLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class AuthSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    organization_name: str | None = Field(default=None, max_length=255)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    organization_name: str | None = None
