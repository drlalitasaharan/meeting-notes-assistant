from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.auth import AuthLogin, AuthResponse, AuthSignup, UserRead
from app.services.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
def signup(payload: AuthSignup, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists.",
        )
    first_name = payload.first_name.strip()
    last_name = payload.last_name.strip()
    if not first_name or not last_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="First name and last name are required.",
        )

    organization_name = None
    if payload.organization_name is not None:
        trimmed_org = payload.organization_name.strip()
        if trimmed_org:
            organization_name = trimmed_org

    user = User(
        email=payload.email.lower().strip(),
        password_hash=hash_password(payload.password),
        first_name=first_name,
        last_name=last_name,
        organization_name=organization_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return AuthResponse(access_token=create_access_token(user=user))


@router.post("/login", response_model=AuthResponse)
def login(payload: AuthLogin, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    return AuthResponse(access_token=create_access_token(user=user))


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        organization_name=current_user.organization_name,
    )
