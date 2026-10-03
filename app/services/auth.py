"""Auth business logic — mirrors RankKW's flow."""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import OtpCode, Session, UsageDaily, User
from ..validators.email import is_valid_email_domain
from .email import send_otp_email, send_welcome_email
from .tokens import create_access_token, create_refresh_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ────────────────────────── Password hashing ──────────────────────────

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_otp(code: str) -> str:
    return pwd_context.hash(code)


def verify_otp(code: str, hashed: str) -> bool:
    return pwd_context.verify(code, hashed)


# ────────────────────────── User operations ──────────────────────────

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    res = await db.execute(select(User).where(User.email == email.lower()))
    return res.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    res = await db.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()


async def create_user(db: AsyncSession, name: str, email: str, password: str) -> User:
    if not is_valid_email_domain(email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Disposable email addresses are not allowed")

    existing = await get_user_by_email(db, email)
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already in use")

    user = User(
        name=name.strip(),
        email=email.lower(),
        password_hash=hash_password(password),
        role="user",
        plan="free",
        is_verified=False,
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return user


# ────────────────────────── OTP operations ──────────────────────────

async def issue_otp(db: AsyncSession, user: User, purpose: str = "reset") -> str:
    """Generate 6-digit OTP, store hash, invalidate previous codes, send email."""
    # Invalidate older codes for same purpose
    await db.execute(
        update(OtpCode)
        .where(OtpCode.user_id == user.id, OtpCode.purpose == purpose, OtpCode.consumed == False)  # noqa: E712
        .values(consumed=True)
    )
    # Generate new
    code = f"{secrets.randbelow(1_000_000):06d}"
    otp = OtpCode(
        user_id=user.id,
        code_hash=hash_otp(code),
        purpose=purpose,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.OTP_TTL_SECONDS),
    )
    db.add(otp)
    await db.flush()
    send_otp_email(user.email, code, purpose=purpose)
    return code


async def consume_otp(db: AsyncSession, user: User, code: str, purpose: str = "reset") -> None:
    """Verify a code and mark consumed. Raises on failure."""
    res = await db.execute(
        select(OtpCode)
        .where(
            OtpCode.user_id == user.id,
            OtpCode.purpose == purpose,
            OtpCode.consumed == False,  # noqa: E712
        )
        .order_by(OtpCode.created_at.desc())
        .limit(1)
    )
    otp = res.scalar_one_or_none()
    if not otp:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No active code — request a new one")
    if otp.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code expired — request a new one")
    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts — request a new code")
    otp.attempts += 1
    if not verify_otp(code, otp.code_hash):
        await db.flush()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid code")
    otp.consumed = True
    await db.flush()


# ────────────────────────── Sessions / refresh ──────────────────────────

async def create_session(db: AsyncSession, user: User, refresh_token: str,
                        user_agent: str | None = None) -> Session:
    import hashlib
    sess = Session(
        user_id=user.id,
        token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc)
        + timedelta(seconds=settings.JWT_REFRESH_TTL_SECONDS),
        user_agent=(user_agent or "")[:500] or None,
    )
    db.add(sess)
    await db.flush()
    return sess


async def issue_tokens_for_user(db: AsyncSession, user: User,
                                user_agent: str | None = None) -> tuple[str, str]:
    access = create_access_token(user)
    refresh = create_refresh_token(user)
    await create_session(db, user, refresh, user_agent)
    return access, refresh


# ────────────────────────── Credits / usage ──────────────────────────

FREE_PLAN_LIMIT = 5


async def get_or_create_usage(db: AsyncSession, user: User) -> UsageDaily:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    res = await db.execute(
        select(UsageDaily).where(UsageDaily.user_id == user.id, UsageDaily.day == today)
    )
    row = res.scalar_one_or_none()
    if not row:
        row = UsageDaily(user_id=user.id, day=today, used=0)
        db.add(row)
        await db.flush()
    return row


async def get_credits_state(db: AsyncSession, user: User) -> dict:
    usage = await get_or_create_usage(db, user)
    limit = FREE_PLAN_LIMIT if user.plan == "free" else 999_999
    return {
        "credits": max(0, limit - usage.used),
        "limit": limit,
        "usedToday": usage.used,
        "plan": user.plan,
        "bonus": None,
    }