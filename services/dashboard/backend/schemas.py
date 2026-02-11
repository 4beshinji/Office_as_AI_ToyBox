from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Task Schemas
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    bounty_gold: int = 10
    bounty_xp: int = 50
    expires_at: Optional[datetime] = None
    task_type: Optional[List[str]] = None
    
    # Intelligent scheduling fields
    urgency: int = 2  # 0-4 (DEFERRED to CRITICAL)
    zone: Optional[str] = None
    min_people_required: int = 1
    estimated_duration: int = 10  # minutes
    
    # Voice data (optional, provided by Brain if voice enabled)
    announcement_audio_url: Optional[str] = None
    announcement_text: Optional[str] = None
    completion_audio_url: Optional[str] = None
    completion_text: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    bounty_gold: Optional[int] = None
    is_completed: Optional[bool] = None
    expires_at: Optional[datetime] = None
    task_type: Optional[List[str]] = None
    urgency: Optional[int] = None
    zone: Optional[str] = None
    is_queued: Optional[bool] = None

class Task(TaskBase):
    id: int
    is_completed: bool
    is_queued: bool = False
    created_at: datetime
    completed_at: Optional[datetime] = None
    dispatched_at: Optional[datetime] = None
    
    # Voice announcement fields
    announcement_audio_url: Optional[str] = None
    announcement_text: Optional[str] = None
    completion_audio_url: Optional[str] = None
    completion_text: Optional[str] = None
    last_reminded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    gold: int
    xp: int
    level: int

    class Config:
        from_attributes = True

# Reward Schemas
class RewardItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    cost_gold: int
    icon: Optional[str] = None

class RewardItemCreate(RewardItemBase):
    pass

class RewardItem(RewardItemBase):
    id: int
    is_available: bool

    class Config:
        from_attributes = True
