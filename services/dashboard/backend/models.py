from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    location = Column(String) # e.g., "Kitchen", "Living Room"
    bounty_gold = Column(Integer, default=10)
    bounty_xp = Column(Integer, default=50)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    gold = Column(Integer, default=0)
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)

class RewardItem(Base):
    __tablename__ = "reward_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    cost_gold = Column(Integer)
    icon = Column(String) # Icon name or URL
    is_available = Column(Boolean, default=True)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("reward_items.id"))
    amount = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
