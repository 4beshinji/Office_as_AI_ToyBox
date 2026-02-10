from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from typing import List
from database import get_db
import models
import json

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
    tasks_db = result.scalars().all()
    
    # Convert DB models to Schema models (handling JSON parsing)
    tasks = []
    for t in tasks_db:
        # Filter out SQLAlchemy internal state and copy dict
        t_dict = {k: v for k, v in t.__dict__.items() if not k.startswith('_')}
        if t.task_type:
            try:
                t_dict['task_type'] = json.loads(t.task_type)
            except:
                t_dict['task_type'] = []
        else:
            t_dict['task_type'] = []
        tasks.append(schemas.Task(**t_dict))
        
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
        expires_at=task.expires_at,
        task_type=json.dumps(task.task_type) if task.task_type else None
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    # Manually construct response dict to handle task_type parsing and avoid __dict__ issues
    response_data = {
        "id": new_task.id,
        "title": new_task.title,
        "description": new_task.description,
        "location": new_task.location,
        "bounty_gold": new_task.bounty_gold,
        "is_completed": new_task.is_completed,
        "created_at": new_task.created_at,
        "completed_at": new_task.completed_at,
        "expires_at": new_task.expires_at,
        "task_type": json.loads(new_task.task_type) if new_task.task_type else []
    }
    
    return schemas.Task(**response_data)

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
