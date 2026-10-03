"""SQLAlchemy ORM models — mirrors the RankKW data contract."""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey, Index, Integer,
    Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uuid() -> str:
    return uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ────────────────────────────── Users & Auth ──────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user")
    plan: Mapped[str] = mapped_column(String(20), default="free")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    otp_codes: Mapped[list["OtpCode"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    usage_daily: Mapped[list["UsageDaily"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def public(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "plan": self.plan,
            "isVerified": self.is_verified,
        }


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped[User] = relationship(back_populates="sessions")


class OtpCode(Base):
    """One row per OTP issuance. Used for both verify-otp and reset."""
    __tablename__ = "otp_codes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(20), default="reset")  # reset | verify
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship(back_populates="otp_codes")


# ────────────────────────────── Credits ──────────────────────────────

class UsageDaily(Base):
    __tablename__ = "usage_daily"
    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_usage_user_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    day: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD (UTC)
    used: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped[User] = relationship(back_populates="usage_daily")


# ────────────────────────────── Keyword Cache ──────────────────────────────

class KeywordSearch(Base):
    """Full response payload cached per (query, geo)."""
    __tablename__ = "keyword_searches"
    __table_args__ = (UniqueConstraint("query", "geo", name="uq_keyword_query_geo"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    geo: Mapped[str] = mapped_column(String(10), default="GLO")
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON blob
    cached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EtsyListing(Base):
    __tablename__ = "etsy_listings"

    listing_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    price_amount: Mapped[int] = mapped_column(Integer, default=0)
    price_divisor: Mapped[int] = mapped_column(Integer, default=100)
    currency_code: Mapped[str] = mapped_column(String(10), default="USD")
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)
    num_favorers: Mapped[int] = mapped_column(Integer, default=0)
    tags_json: Mapped[str] = mapped_column(Text, default="[]")
    images_json: Mapped[str] = mapped_column(Text, default="[]")
    url: Mapped[str] = mapped_column(Text, default="")
    shop_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    shop_name: Mapped[str] = mapped_column(String(255), default="")
    taxonomy_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state: Mapped[str] = mapped_column(String(20), default="active")
    created_timestamp: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    processing_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class KeywordListing(Base):
    """Which listings ranked for which (query, geo) at what position."""
    __tablename__ = "keyword_listings"
    __table_args__ = (
        Index("ix_kwlist_query_geo", "query", "geo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    geo: Mapped[str] = mapped_column(String(10), default="GLO")
    listing_id: Mapped[int] = mapped_column(BigInteger, index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ────────────────────────────── Alerts (in-app inbox) ──────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    type: Mapped[str] = mapped_column(String(20), default="info")  # chat | info
    title: Mapped[str] = mapped_column(String(255), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    link: Mapped[str | None] = mapped_column(Text, nullable=True)
    audience: Mapped[str] = mapped_column(String(20), default="all")
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)