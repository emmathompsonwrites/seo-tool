"""Environment-driven configuration."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "EtsyRankEngine"
    APP_ENV: str = "development"
    APP_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    # JWT
    JWT_ACCESS_SECRET: str = "dev-access-secret-change-in-production-32"
    JWT_REFRESH_SECRET: str = "dev-refresh-secret-change-in-production-32"
    JWT_ACCESS_TTL_SECONDS: int = 900
    JWT_REFRESH_TTL_SECONDS: int = 2_592_000
    JWT_ALGORITHM: str = "HS256"

    # DB
    DATABASE_URL: str = "sqlite+aiosqlite:///./etsy_rank.db"

    # Email
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "EtsyRank <noreply@example.com>"

    # reCAPTCHA
    RECAPTCHA_SECRET: str = ""
    RECAPTCHA_ENABLED: bool = False

    # Etsy
    ETSY_KEYSTRING: str = ""
    ETSY_SHARED_SECRET: str = ""

    # OTP
    OTP_TTL_SECONDS: int = 300
    OTP_MAX_ATTEMPTS: int = 5

    # Demo mode — serve fixture data instead of calling Etsy (for frontend dev)
    DEMO_MODE: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()