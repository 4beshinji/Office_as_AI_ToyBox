"""
Task priority and urgency definitions.
"""
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional
import time


class TaskUrgency(IntEnum):
    """Task urgency levels (0-4)."""
    DEFERRED = 0      # Can wait indefinitely (e.g., "organize files")
    LOW = 1           # Can wait hours/days (e.g., "restock supplies")
    NORMAL = 2        # Should be done today (e.g., "clean whiteboard")
    HIGH = 3          # Should be done within hours (e.g., "fix printer")
    CRITICAL = 4      # Must be done immediately (e.g., "safety issue")


@dataclass
class QueuedTask:
    """
    Task in the priority queue with computed priority.
    """
    task_id: int
    title: str
    urgency: TaskUrgency
    zone: Optional[str]
    min_people_required: int
    estimated_duration: int  # minutes
    created_at: float  # Unix timestamp
    deadline: Optional[float] = None  # Unix timestamp
    
    def compute_priority(self) -> float:
        """
        Compute priority score for queue ordering.
        Higher score = higher priority.
        
        Priority factors:
        1. Base urgency (0-4) * 1000
        2. Age penalty: +1 per hour waiting
        3. Deadline proximity: +100 if within 2 hours
        """
        current_time = time.time()
        
        # Base urgency (0-4000)
        priority = int(self.urgency) * 1000
        
        # Age penalty (waiting time in hours)
        hours_waiting = (current_time - self.created_at) / 3600
        priority += hours_waiting
        
        # Deadline proximity bonus
        if self.deadline:
            hours_until_deadline = (self.deadline - current_time) / 3600
            if hours_until_deadline < 2:
                priority += 100
            elif hours_until_deadline < 6:
                priority += 50
        
        return priority
    
    def is_stale(self, max_age_hours: float = 24) -> bool:
        """Check if task has been waiting too long."""
        age_hours = (time.time() - self.created_at) / 3600
        return age_hours > max_age_hours
    
    def __lt__(self, other):
        """For priority queue comparison (higher priority first)."""
        return self.compute_priority() > other.compute_priority()
