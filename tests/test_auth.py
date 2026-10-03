"""Smoke tests for the full auth flow."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200


async def test_register_and_login(client):
    payload = {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "TestPass123!",
        "confirmPassword": "TestPass123!",
    }
    r = await client.post("/api/auth/register", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    assert body["data"]["email"] == "testuser@example.com"
    assert "sr_access" in r.cookies
    assert "sr_refresh" in r.cookies

    # Login
    r2 = await client.post("/api/auth/login", json={
        "email": "testuser@example.com",
        "password": "TestPass123!",
    })
    assert r2.status_code == 200


async def test_register_weak_password_rejected(client):
    r = await client.post("/api/auth/register", json={
        "name": "Weak",
        "email": "weak@example.com",
        "password": "short",
        "confirmPassword": "short",
    })
    assert r.status_code == 422


async def test_register_disposable_email_rejected(client):
    r = await client.post("/api/auth/register", json={
        "name": "Spam",
        "email": "test@mailinator.com",
        "password": "TestPass123!",
        "confirmPassword": "TestPass123!",
    })
    assert r.status_code == 422


async def test_check_email(client):
    r = await client.get("/api/auth/check-email", params={"email": "new@example.com"})
    assert r.status_code == 200
    assert r.json()["valid"] is True
    assert r.json()["exists"] is False


async def test_forgot_and_reset_flow(client):
    # Register
    await client.post("/api/auth/register", json={
        "name": "Reset Test",
        "email": "reset@example.com",
        "password": "TestPass123!",
        "confirmPassword": "TestPass123!",
    })
    # Forgot
    r = await client.post("/api/auth/forgot-password", json={"email": "reset@example.com"})
    assert r.status_code == 200
    # In dev mode (no Resend key), the OTP is logged to console.
    # For test, we'd need to read the DB directly — omitted here.