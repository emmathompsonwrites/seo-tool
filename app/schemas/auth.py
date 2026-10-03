"""Request/response models — 1:1 mirror of RankKW's Zod schemas."""
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from ..validators.email import is_valid_email_domain
from ..validators.password import validate_password


# ────────────────────────────── Requests ──────────────────────────────

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=60, description="Full name (2-60 chars)")
    email: EmailStr
    password: str
    confirmPassword: str

    @field_validator("email")
    @classmethod
    def _email_rules(cls, v: str) -> str:
        v = v.lower()
        if not is_valid_email_domain(v):
            raise ValueError("Disposable email addresses are not allowed")
        return v

    @field_validator("password")
    @classmethod
    def _password_rules(cls, v: str) -> str:
        return validate_password(v)

    @model_validator(mode="after")
    def _passwords_match(self):
        if self.password != self.confirmPassword:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    recaptchaToken: str | None = None

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.lower()


class ForgotRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.lower()


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.lower()


class ResetRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
    password: str
    confirmPassword: str

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.lower()

    @field_validator("password")
    @classmethod
    def _password_rules(cls, v: str) -> str:
        return validate_password(v)

    @model_validator(mode="after")
    def _passwords_match(self):
        if self.password != self.confirmPassword:
            raise ValueError("Passwords do not match")
        return self


# ────────────────────────────── Responses ──────────────────────────────

class PublicUser(BaseModel):
    id: str
    name: str
    email: str
    role: str
    plan: str
    isVerified: bool


class AuthResponse(BaseModel):
    success: bool = True
    data: PublicUser


class CheckEmailResponse(BaseModel):
    valid: bool
    exists: bool = False


class SimpleMessage(BaseModel):
    success: bool = True
    message: str = "OK"