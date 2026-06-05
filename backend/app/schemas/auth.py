from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class AuthLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class AuthSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: int
    email: EmailStr
