"""JWT issuance + cookie helpers — mirrors RankKW's cookie flags exactly."""
from datetime import datetime, timedelta, timezone

from fastapi import Response
from jose import JWTError, jwt

from ..config import settings


def create_access_token(user) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "plan": user.plan,
        "isVerified": user.is_verified,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.JWT_ACCESS_TTL_SECONDS)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_ACCESS_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.JWT_REFRESH_TTL_SECONDS)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_REFRESH_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_ACCESS_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def decode_refresh_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_REFRESH_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Sets both cookies with the exact flags RankKW uses.
    Secure is enabled only in production so dev over HTTP works."""
    secure = settings.APP_ENV == "production"
    response.set_cookie(
        key="sr_access",
        value=access_token,
        max_age=settings.JWT_ACCESS_TTL_SECONDS,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key="sr_refresh",
        value=refresh_token,
        max_age=settings.JWT_REFRESH_TTL_SECONDS,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    secure = settings.APP_ENV == "production"
    response.delete_cookie(
        "sr_access", path="/", secure=secure, httponly=True, samesite="lax"
    )
    response.delete_cookie(
        "sr_refresh", path="/", secure=secure, httponly=True, samesite="lax"
    )