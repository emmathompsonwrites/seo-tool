"""
Rank tracking — requires listing_snapshots table (Stage 5).
Stubbed until the data moat exists.
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.routes.auth import current_user

router = APIRouter(prefix="/api/etsy", tags=["etsy"])


@router.get("/rank-movers")
async def rank_movers(
    request: Request,
    q: str = Query(..., min_length=1),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    user = await current_user(request, db)
    return {
        "movers": [],
        "reliable": False,
        "reason": (
            "Rank tracking requires historical snapshots. "
            "Run the daily cron (Stage 5) to populate listing_snapshots."
        ),
        "country": "US",
        "coverage": 0,
        "signals": {},
    }