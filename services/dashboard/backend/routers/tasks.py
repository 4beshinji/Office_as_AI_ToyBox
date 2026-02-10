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

import schemas

@router.get("/", response_model=List[schemas.Task])
async def read_tasks(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # Filter out expired tasks
    query = select(models.Task).filter(
        (models.Task.expires_at == None) | (models.Task.expires_at > func.now())
    ).offset(skip).limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()
    return tasks

@router.post("/", response_model=schemas.Task)
async def create_task(task: schemas.TaskCreate, db: AsyncSession = Depends(get_db)):
    # Duplicate Check: Check for active tasks with same title and location
    query = select(models.Task).filter(
        models.Task.title == task.title,
        models.Task.location == task.location,
        models.Task.is_completed == False
    )
    result = await db.execute(query)
    existing_task = result.scalars().first()

    if existing_task:
        # Delete existing active task to "update" it (or avoid duplication)
        await db.delete(existing_task)
        await db.commit()

    new_task = models.Task(
        title=task.title,
        description=task.description,
        location=task.location,
        bounty_gold=task.bounty_gold,
        bounty_xp=task.bounty_xp,
        expires_at=task.expires_at,
        task_type=task.task_type
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task

@router.put("/{task_id}/complete", response_model=schemas.Task)
async def complete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Task).filter(models.Task.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.is_completed = True
    task.completed_at = func.now()
    await db.commit()
    await db.refresh(task)
    return task
