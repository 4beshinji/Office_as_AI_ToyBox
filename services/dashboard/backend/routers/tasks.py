from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from database import get_db
import models

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)

@router.get("/", response_model=List[dict]) # Use Pydantic models in real app
async def read_tasks(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Task).offset(skip).limit(limit))
    tasks = result.scalars().all()
    return tasks

@router.post("/")
async def create_task(title: str, description: str, bounty: int, db: AsyncSession = Depends(get_db)):
    new_task = models.Task(title=title, description=description, bounty_amount=bounty)
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task
