# app/deps.py
from fastapi import Header, HTTPException, status

async def demo_auth_dependency(authorization: str | None = Header(default=None)):
    """
    Phase-1 placeholder: require a header but don't verify it.
    Switch off by removing the override in main.py.
    """
    if authorization is None or not authorization.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )
    return True

