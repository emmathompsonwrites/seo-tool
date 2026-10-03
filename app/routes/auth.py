"""All /api/auth/* endpoints — 1:1 with RankKW."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import User
from ..schemas.auth import (
    AuthResponse, CheckEmailResponse, ForgotRequest, LoginRequest,
    RegisterRequest, ResetRequest, SimpleMessage, VerifyOtpRequest,
)
from ..services import auth as auth_svc
from ..services.tokens import (
    clear_auth_cookies, decode_refresh_token, set_auth_cookies,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ────────────────────────── Utilities ──────────────────────────

async def current_user(request: Request, db: AsyncSession) -> User:
    from ..services.tokens import decode_access_token
    print("=" * 60)
    print("[DEBUG current_user] Called")
    print("[DEBUG] All cookies:", dict(request.cookies))
    print("[DEBUG] All headers:", dict(request.headers))
    token = request.cookies.get("sr_access")
    print("[DEBUG] sr_access present:", bool(token))
    if token:
        print("[DEBUG] sr_access first 40:", token[:40])
        payload = decode_access_token(token)
        print("[DEBUG] payload decoded:", payload)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = await auth_svc.get_user_by_id(db, payload["id"])
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


# ────────────────────────── Endpoints ──────────────────────────

@router.get("/check-email", response_model=CheckEmailResponse)
async def check_email(email: str, db: AsyncSession = Depends(get_db)):
    """Client calls this debounced (450ms)."""
    from ..validators.email import is_valid_email_domain
    from ..validators.password import _UPPER  # noqa: F401 — placeholder
    email = (email or "").strip().lower()
    if "@" not in email or not is_valid_email_domain(email):
        return {"valid": False, "exists": False}
    user = await auth_svc.get_user_by_email(db, email)
    return {"valid": True, "exists": user is not None}


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, request: Request, response: Response,
                   db: AsyncSession = Depends(get_db)):
    user = await auth_svc.create_user(db, req.name, req.email, req.password)
    # Issue tokens + session
    access, refresh = await auth_svc.issue_tokens_for_user(
        db, user, user_agent=request.headers.get("user-agent")
    )
    set_auth_cookies(response, access, refresh)
    await db.commit()
    # Fire-and-forget welcome email (best effort)
    try:
        from ..services.email import send_welcome_email
        send_welcome_email(user.email, user.name)
    except Exception:
        pass
    return {"success": True, "data": user.public()}


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, request: Request, response: Response,
                db: AsyncSession = Depends(get_db)):
    user = await auth_svc.authenticate_user(db, req.email, req.password)
    access, refresh = await auth_svc.issue_tokens_for_user(
        db, user, user_agent=request.headers.get("user-agent")
    )
    set_auth_cookies(response, access, refresh)
    await db.commit()
    return {"success": True, "data": user.public()}


@router.post("/forgot-password", response_model=SimpleMessage)
async def forgot_password(req: ForgotRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_svc.get_user_by_email(db, req.email)
    if user:
        await auth_svc.issue_otp(db, user, purpose="reset")
        await db.commit()
    # Always return success to avoid leaking whether email exists
    return {"success": True, "message": "If that email is registered, a code has been sent."}


@router.post("/verify-otp", response_model=SimpleMessage)
async def verify_otp(req: VerifyOtpRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_svc.get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid code")
    await auth_svc.consume_otp(db, user, req.code, purpose="reset")
    await db.commit()
    return {"success": True, "message": "Code verified."}


@router.post("/reset-password", response_model=SimpleMessage)
async def reset_password(req: ResetRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_svc.get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid request")
    # Verify code again (single-use)
    await auth_svc.consume_otp(db, user, req.code, purpose="reset")
    user.password_hash = auth_svc.hash_password(req.password)
    await db.commit()
    return {"success": True, "message": "Password updated."}


@router.post("/logout", response_model=SimpleMessage)
async def logout(response: Response):
    clear_auth_cookies(response)
    return {"success": True, "message": "Logged out."}


@router.post("/refresh", response_model=SimpleMessage)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("sr_refresh")
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No refresh token")
    payload = decode_refresh_token(token)
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    user = await auth_svc.get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    access, refresh_tok = await auth_svc.issue_tokens_for_user(db, user)
    set_auth_cookies(response, access, refresh_tok)
    await db.commit()
    return {"success": True, "message": "Refreshed."}


@router.get("/oauth/{provider}")
async def oauth_start(provider: str, redirect: str = "/dashboard"):
    """
    Stub — implement per provider (Google, GitHub, etc.).
    RankKW redirects to /api/auth/oauth/<provider>?redirect=<path>.
    """
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        f"OAuth provider '{provider}' not yet wired. Redirect target: {redirect}",
    )