from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import database
import models
import schemas

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

@router.get("/", response_model=List[schemas.Task])
async def read_tasks(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Task).offset(skip).limit(limit))
    tasks = result.scalars().all()
    return tasks

@router.post("/", response_model=schemas.Task)
async def create_task(task: schemas.TaskCreate, db: AsyncSession = Depends(database.get_db)):
    db_task = models.Task(**task.model_dump())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

@router.get("/{task_id}", response_model=schemas.Task)
async def read_task(task_id: int, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Task).filter(models.Task.id == task_id))
    task = result.scalars().first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=schemas.Task)
async def update_task(task_id: int, task: schemas.TaskUpdate, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Task).filter(models.Task.id == task_id))
    db_task = result.scalars().first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    await db.commit()
    await db.refresh(db_task)
    return db_task

@router.delete("/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Task).filter(models.Task.id == task_id))
    db_task = result.scalars().first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(db_task)
    await db.commit()
    return {"ok": True}
