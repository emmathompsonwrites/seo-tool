"""
Keyword research endpoints — mirrors RankKW's /api/keywords contract.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.routes.auth import current_user
from app.services.etsy import get_etsy_client
from app.services.scoring import (
    analyze_listings,
    difficulty_label,
    fav_per_view,
    heat_color,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.get("")
async def keywords(
    request: Request,
    q: str = Query(..., min_length=1),
    geo: str = Query("US"),
    db: AsyncSession = Depends(get_db),
):
    """
    Main keyword research endpoint.
    Returns: stats, related keywords, listings, analysis, credits state.
    """
    user = await current_user(request, db)

    # ── DEMO MODE ─────────────────────────────────────────────────
    if settings.DEMO_MODE:
        logger.info("[DEMO] /api/keywords q=%r geo=%r", q, geo)
        from app.services.demo_data import demo_keyword_response
        return demo_keyword_response(q, geo)
    # ──────────────────────────────────────────────────────────────

    etsy = get_etsy_client()

    try:
        resp = await etsy.search_listings(keywords=q, limit=100)
    except Exception as e:
        logger.exception("Etsy upstream error")
        raise HTTPException(
            status_code=502,
            detail=f"Etsy upstream error: {type(e).__name__}: {e}",
        )

    if "error" in resp:
        raise HTTPException(status_code=502, detail=f"Etsy API error: {resp['error']}")

    listings = resp.get("results") or []

    total_results = resp.get("count", len(listings))
    views = [l.get("views", 0) or 0 for l in listings]
    hearts = [l.get("num_favorers", 0) or 0 for l in listings]
    avg_views = sum(views) / len(views) if views else 0
    avg_hearts = sum(hearts) / len(hearts) if hearts else 0

    competition_density = total_results / max(1, len(listings))
    difficulty = min(100, max(0, 50 + (competition_density - 5) * 2))

    prices = []
    for l in listings:
        p = l.get("price", {})
        if p.get("amount") is not None:
            prices.append(p["amount"] / p.get("divisor", 100))
    avg_price = sum(prices) / len(prices) if prices else 0

    stats = {
        "avgViews": round(avg_views, 1),
        "avgFavorites": round(avg_hearts, 1),
        "favPerView": round(fav_per_view(avg_hearts, avg_views), 2),
        "etsyCompetition": heat_color(min(100, competition_density * 10)),
        "totalResults": total_results,
        "difficulty": round(difficulty, 1),
        "difficultyLabel": difficulty_label(difficulty),
        "avgPrice": round(avg_price, 2),
        "currency": "USD",
        "googleSearches": None,
        "googleStatus": "unavailable",
        "googleCompetition": None,
        "googleCompetitionIndex": None,
        "googleCpcLow": None,
        "googleCpcHigh": None,
        "googleCurrency": None,
    }

    return {
        "success": True,
        "cached": False,
        "data": {
            "query": q,
            "stats": stats,
            "related": [],
            "listings": listings,
            "analysis": analyze_listings(listings),
            "cachedAt": None,
        },
        "searches": {"used": 0, "limit": 5},
        "state": {"credits": 0, "limit": 5, "usedToday": 0, "plan": "free", "bonus": 0},
    }