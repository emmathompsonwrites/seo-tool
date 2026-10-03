"""
Alerts inbox — local-only for now.
RankKW's alerts are server-pushed; ours are generated on-demand.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.routes.auth import current_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    user = await current_user(request, db)
    return {
        "items": [],
        "unread": 0,
        "hasMore": False,
    }