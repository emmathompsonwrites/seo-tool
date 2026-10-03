"""
Google Trends endpoints — mirrors RankKW's /api/trends contract.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.routes.auth import current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("")
async def trends(
    request: Request,
    q: str = Query(..., min_length=1),
    geo: str = Query("US"),
    db: AsyncSession = Depends(get_db),
):
    user = await current_user(request, db)

    # ── DEMO MODE ─────────────────────────────────────────────────
    if settings.DEMO_MODE:
        logger.info("[DEMO] /api/trends q=%r geo=%r", q, geo)
        from app.services.demo_data import demo_trends_response
        return demo_trends_response(q, geo)
    # ──────────────────────────────────────────────────────────────

    points: list[dict] = []
    google_available = False
    note = None

    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        await asyncio.to_thread(
            pytrends.build_payload, [q], cat=0, timeframe="today 5-y", geo=geo
        )
        df = await asyncio.to_thread(pytrends.interest_over_time)

        if not df.empty:
            for ts, row in df.iterrows():
                points.append({"month": ts.strftime("%Y-%m"), "value": int(row[q])})
            google_available = True
    except Exception as e:
        note = f"Google Trends unavailable: {type(e).__name__}"

    return {
        "trends": [{"platform": "google", "points": points}],
        "countries": [],
        "supplyByMonth": [],
        "market": {
            "sample": 0,
            "currency": "USD",
            "priceMin": 0, "priceMax": 0, "priceMedian": 0,
            "priceP25": 0, "priceP75": 0,
            "priceBands": [],
            "viewsMedian": 0, "viewsMax": 0,
            "favMedian": 0, "favTotal": 0,
            "engagementPct": 0,
            "topTags": [], "topListings": [],
        },
        "googleAvailable": google_available,
        "note": note,
        "googleStatus": "available" if google_available else "unavailable",
        "marketplaceAvailable": False,
    }


@router.get("/countries")
async def trend_countries(
    request: Request,
    q: str = Query("", min_length=0),
    db: AsyncSession = Depends(get_db),
):
    user = await current_user(request, db)
    return {"suggestions": []}