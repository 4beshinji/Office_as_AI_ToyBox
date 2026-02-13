from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models import SupplyStats, RewardRate
from schemas import SupplyResponse, RewardRateResponse, RewardRateUpdate

router = APIRouter(tags=["admin"])


@router.get("/supply", response_model=SupplyResponse)
async def get_supply(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupplyStats))
    stats = result.scalars().first()
    if not stats:
        return SupplyResponse(total_issued=0, total_burned=0, circulating=0)
    return stats


@router.get("/reward-rates", response_model=List[RewardRateResponse])
async def list_reward_rates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RewardRate).order_by(RewardRate.device_type))
    return result.scalars().all()


@router.put("/reward-rates/{device_type}", response_model=RewardRateResponse)
async def update_reward_rate(
    device_type: str,
    body: RewardRateUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RewardRate).filter(RewardRate.device_type == device_type)
    )
    rate = result.scalars().first()
    if not rate:
        raise HTTPException(status_code=404, detail="Reward rate not found")

    rate.rate_per_hour = body.rate_per_hour
    if body.min_uptime_for_reward is not None:
        rate.min_uptime_for_reward = body.min_uptime_for_reward

    await db.commit()
    await db.refresh(rate)
    return rate
