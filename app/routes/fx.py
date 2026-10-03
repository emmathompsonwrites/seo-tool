"""
FX conversion — thin wrapper over frankfurter.app (free, no key).
Falls back to fixture rates when DEMO_MODE=True.
"""
from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.routes.auth import current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fx", tags=["fx"])

FRANKFURTER_BASE = "https://api.frankfurter.app"


@router.get("")
async def fx(
    request: Request,
    frm: str = Query("PKR", alias="from"),
    to: str = Query("USD"),
    db: AsyncSession = Depends(get_db),
):
    user = await current_user(request, db)

    # ── DEMO MODE ─────────────────────────────────────────────────
    if settings.DEMO_MODE:
        logger.info("[DEMO] /api/fx %s→%s", frm, to)
        from app.services.demo_data import demo_fx_response
        return demo_fx_response(frm, to)
    # ──────────────────────────────────────────────────────────────

    if frm.upper() == to.upper():
        return {
            "success": True,
            "data": {"from": frm.upper(), "to": to.upper(), "rate": 1.0},
            "cached": False,
        }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{FRANKFURTER_BASE}/latest",
                params={"from": frm.upper(), "to": to.upper()},
            )
            resp.raise_for_status()
            data = resp.json()
            rate = data.get("rates", {}).get(to.upper())
            if rate is None:
                raise HTTPException(
                    status_code=502, detail="Rate not returned by provider"
                )
            return {
                "success": True,
                "data": {"from": frm.upper(), "to": to.upper(), "rate": float(rate)},
                "cached": False,
            }
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502, detail=f"FX provider error: {e.response.status_code}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502, detail=f"FX provider unreachable: {e.__class__.__name__}"
            )