"""Email delivery via Resend. Falls back to console in dev if no key."""
import logging

import resend

from ..config import settings

log = logging.getLogger(__name__)


def _send(to: str, subject: str, html: str) -> None:
    if not settings.RESEND_API_KEY:
        log.warning("[DEV EMAIL] to=%s subject=%s\n%s", to, subject, html)
        return
    resend.api_key = settings.RESEND_API_KEY
    resend.Emails.send({
        "from": settings.EMAIL_FROM,
        "to": to,
        "subject": subject,
        "html": html,
    })


def send_otp_email(to: str, code: str, purpose: str = "reset") -> None:
    subject = "Your Rank Engine verification code"
    html = f"""
    <div style="font-family:system-ui,sans-serif;max-width:480px;margin:auto;padding:24px">
      <h2 style="color:#3D3E3B;margin:0 0 8px">Verification code</h2>
      <p style="color:#6E6E64;margin:0 0 20px">
        Use this code to continue. It expires in {settings.OTP_TTL_SECONDS // 60} minutes.
      </p>
      <div style="font-size:32px;font-weight:700;letter-spacing:8px;color:#FB5E09;
                  background:#F5F5EB;padding:16px;text-align:center;border-radius:8px">
        {code}
      </div>
      <p style="color:#919183;font-size:12px;margin-top:20px">
        If you didn't request this, ignore this email.
      </p>
    </div>
    """
    _send(to, subject, html)


def send_welcome_email(to: str, name: str) -> None:
    subject = "Welcome to Rank Engine"
    html = f"""
    <div style="font-family:system-ui,sans-serif;max-width:480px;margin:auto;padding:24px">
      <h2 style="color:#3D3E3B;margin:0 0 8px">Hi {name},</h2>
      <p style="color:#6E6E64">Thanks for signing up. Your account is ready.</p>
      <p style="color:#6E6E64">You're on the free plan — 5 keyword searches per day.</p>
    </div>
    """
    _send(to, subject, html)