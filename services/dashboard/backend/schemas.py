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
    task_type: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    bounty_gold: Optional[int] = None
    bounty_xp: Optional[int] = None
    is_completed: Optional[bool] = None
    expires_at: Optional[datetime] = None
    task_type: Optional[str] = None

class Task(TaskBase):
    id: int
    is_completed: bool
    created_at: datetime
    completed_at: Optional[datetime] = None

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
