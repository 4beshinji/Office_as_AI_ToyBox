from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import database
import models
import schemas

router = APIRouter()

# --- Users ---
@router.get("/users/me", response_model=schemas.User, tags=["users"])
async def read_user_me(db: AsyncSession = Depends(database.get_db)):
    # Create default user if not exists (Single user mode)
    result = await db.execute(select(models.User).filter(models.User.username == "human"))
    user = result.scalars().first()
    if not user:
        user = models.User(username="human", gold=0, xp=0, level=1)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user

# --- Rewards ---
@router.get("/rewards/", response_model=List[schemas.RewardItem], tags=["rewards"])
async def read_rewards(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.RewardItem))
    return result.scalars().all()

@router.post("/rewards/", response_model=schemas.RewardItem, tags=["rewards"])
async def create_reward(item: schemas.RewardItemCreate, db: AsyncSession = Depends(database.get_db)):
    db_item = models.RewardItem(**item.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item
