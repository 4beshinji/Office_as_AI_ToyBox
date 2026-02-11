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
        task_type=json.dumps(task.task_type) if task.task_type else None,
        urgency=task.urgency,
        zone=task.zone,
        min_people_required=task.min_people_required,
        estimated_duration=task.estimated_duration,
        is_queued=False,  # New tasks default to not queued
        dispatched_at=func.now(),  # Mark as dispatched immediately
        # Voice data (if provided by Brain)
        announcement_audio_url=getattr(task, 'announcement_audio_url', None),
        announcement_text=getattr(task, 'announcement_text', None),
        completion_audio_url=getattr(task, 'completion_audio_url', None),
        completion_text=getattr(task, 'completion_text', None)
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
        "is_queued": new_task.is_queued,
        "created_at": new_task.created_at,
        "completed_at": new_task.completed_at,
        "dispatched_at": new_task.dispatched_at,
        "expires_at": new_task.expires_at,
        "task_type": json.loads(new_task.task_type) if new_task.task_type else [],
        "urgency": new_task.urgency,
        "zone": new_task.zone,
        "min_people_required": new_task.min_people_required,
        "estimated_duration": new_task.estimated_duration,
        "announcement_audio_url": new_task.announcement_audio_url,
        "announcement_text": new_task.announcement_text,
        "completion_audio_url": new_task.completion_audio_url,
        "completion_text": new_task.completion_text,
        "last_reminded_at": new_task.last_reminded_at
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

@router.put("/{task_id}/reminded", response_model=schemas.Task)
async def mark_task_reminded(task_id: int, db: AsyncSession = Depends(get_db)):
    """Update the last_reminded_at timestamp for a task."""
    result = await db.execute(select(models.Task).filter(models.Task.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.last_reminded_at = func.now()
    await db.commit()
    await db.refresh(task)
    return task
# Queue Management Endpoints

@router.get("/queue", response_model=List[schemas.Task])
async def get_queued_tasks(db: AsyncSession = Depends(get_db)):
    """Get all queued tasks (not yet dispatched to dashboard)."""
    query = select(models.Task).filter(models.Task.is_queued == True).order_by(models.Task.urgency.desc(), models.Task.created_at)
    result = await db.execute(query)
    tasks_db = result.scalars().all()
    
    tasks = []
    for t in tasks_db:
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


@router.put("/{task_id}/dispatch", response_model=schemas.Task)
async def dispatch_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a queued task as dispatched (send to dashboard)."""
    result = await db.execute(select(models.Task).filter(models.Task.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.is_queued = False
    task.dispatched_at = func.now()
    await db.commit()
    await db.refresh(task)
    
    t_dict = {k: v for k, v in task.__dict__.items() if not k.startswith('_')}
    if task.task_type:
        try:
            t_dict['task_type'] = json.loads(task.task_type)
        except:
            t_dict['task_type'] = []
    else:
        t_dict['task_type'] = []
    
    return schemas.Task(**t_dict)


@router.get("/stats")
async def get_task_stats(db: AsyncSession = Depends(get_db)):
    """Get task statistics."""
    # Queued tasks count
    queued_query = select(func.count()).select_from(models.Task).filter(models.Task.is_queued == True)
    queued_result = await db.execute(queued_query)
    queued_count = queued_result.scalar()
    
    # Completed tasks in last hour
    completed_query = select(func.count()).select_from(models.Task).filter(
        models.Task.is_completed == True,
        models.Task.completed_at >= func.datetime('now', '-1 hour')
    )
    completed_result = await db.execute(completed_query)
    completed_last_hour = completed_result.scalar()
    
    # Active (dispatched but not completed)
    active_query = select(func.count()).select_from(models.Task).filter(
        models.Task.is_completed == False,
        models.Task.is_queued == False
    )
    active_result = await db.execute(active_query)
    active_count = active_result.scalar()
    
    return {
        "tasks_queued": queued_count or 0,
        "tasks_active": active_count or 0,
        "tasks_completed_last_hour": completed_last_hour or 0
    }
