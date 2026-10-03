"""Credits mirror — matches RankKW's /api/credits/* endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..services import auth as auth_svc
from ..routes.auth import current_user

router = APIRouter(prefix="/api/credits", tags=["credits"])


@router.post("/check")
async def check_credits(payload: dict, request: Request, db: AsyncSession = Depends(get_db)):
    user = await current_user(request, db)
    state = await auth_svc.get_credits_state(db, user)
    if state["credits"] <= 0:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "credit_limit",
                "error": "You've used all of today's credits.",
                "state": state,
                "plan": user.plan,
            },
        )
    return {"success": True, "state": state}


@router.post("/charge")
async def charge_credits(payload: dict, request: Request, db: AsyncSession = Depends(get_db)):
    user = await current_user(request, db)
    usage = await auth_svc.get_or_create_usage(db, user)
    limit = auth_svc.FREE_PLAN_LIMIT if user.plan == "free" else 999_999
    if usage.used >= limit:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "credit_limit",
                "error": "Credit limit reached.",
                "state": await auth_svc.get_credits_state(db, user),
                "plan": user.plan,
            },
        )
    usage.used += 1
    await db.commit()
    return {"success": True, "charged": True, "state": await auth_svc.get_credits_state(db, user)}


@router.post("/refund")
async def refund_credits(payload: dict, request: Request, db: AsyncSession = Depends(get_db)):
    user = await current_user(request, db)
    usage = await auth_svc.get_or_create_usage(db, user)
    if usage.used > 0:
        usage.used -= 1
        await db.commit()
    return {"success": True, "refunded": True, "state": await auth_svc.get_credits_state(db, user)}