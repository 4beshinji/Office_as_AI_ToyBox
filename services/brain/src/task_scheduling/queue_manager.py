"""
Task Queue Manager for intelligent task scheduling.
"""
import heapq
from typing import Optional, List
from loguru import logger
import time

from .priority import TaskUrgency, QueuedTask
from .decision import TaskDispatchDecision


class TaskQueueManager:
    """
    Manages task queue with intelligent dispatching based on context.
    """
    
    def __init__(self, world_model, dashboard_client):
        self.world_model = world_model
        self.dashboard = dashboard_client
        self.decision_engine = TaskDispatchDecision(world_model)
        
        # Priority queue (min-heap, but QueuedTask.__lt__ reverses it)
        self.queue: List[QueuedTask] = []
        
        # Tracking
        self.last_process_time = time.time()
    
    async def add_task(
        self,
        task_id: int,
        title: str,
        urgency: int,
        zone: Optional[str] = None,
        min_people_required: int = 1,
        estimated_duration: int = 10,
        deadline: Optional[float] = None,
        interruptible: bool = True
    ):
        """
        Add a task to the system. Either dispatch immediately or queue.
        
        Args:
            task_id: Dashboard task ID
            title: Task title
            urgency: Task urgency (0-4)
            zone: Target zone
            min_people_required: Minimum people needed
            estimated_duration: Estimated duration (minutes)
            deadline: Unix timestamp deadline
            interruptible: Can interrupt focused users
        """
        
        # Decide whether to dispatch now or queue
        should_dispatch, reason = self.decision_engine.should_dispatch_now(
            urgency=urgency,
            zone=zone,
            min_people_required=min_people_required,
            interruptible=interruptible
        )
        
        if should_dispatch:
            logger.info(f"✅ Dispatching task immediately: '{title}' - {reason}")
            # Task is already dispatched by default in create_task
            # No action needed here
        else:
            logger.info(f"⏸️  Queuing task: '{title}' - {reason}")
            
            # Create queued task
            queued_task = QueuedTask(
                task_id=task_id,
                title=title,
                urgency=TaskUrgency(urgency),
                zone=zone,
                min_people_required=min_people_required,
                estimated_duration=estimated_duration,
                created_at=time.time(),
                deadline=deadline
            )
            
            # Add to priority queue
            heapq.heappush(self.queue, queued_task)
            
            # Update task status in dashboard
            await self._update_task_queue_status(task_id, is_queued=True)
            
            # Log optimal conditions
            optimal = self.decision_engine.get_optimal_dispatch_conditions(
                urgency, zone, min_people_required
            )
            logger.debug(f"Optimal dispatch conditions: {optimal}")
    
    async def process_queue(self):
        """
        Periodically check if queued tasks can be dispatched.
        Should be called every ~30 seconds.
        """
        if not self.queue:
            return
        
        logger.debug(f"Processing queue: {len(self.queue)} tasks waiting")
        
        # Check each task in priority order
        tasks_to_dispatch = []
        remaining_tasks = []
        
        while self.queue:
            task = heapq.heappop(self.queue)
            
            # Check if conditions are now met
            should_dispatch, reason = self.decision_engine.should_dispatch_now(
                urgency=int(task.urgency),
                zone=task.zone,
                min_people_required=task.min_people_required
            )
            
            if should_dispatch:
                logger.info(f"✅ Dispatching queued task: '{task.title}' - {reason}")
                tasks_to_dispatch.append(task)
            elif task.is_stale(max_age_hours=24):
                # Force dispatch stale tasks (been queued > 24 hours)
                logger.warning(f"⚠️  Force dispatching stale task: '{task.title}' (queued for 24h)")
                tasks_to_dispatch.append(task)
            else:
                remaining_tasks.append(task)
        
        # Dispatch selected tasks
        for task in tasks_to_dispatch:
            await self._dispatch_task(task)
        
        # Re-queue remaining tasks
        for task in remaining_tasks:
            heapq.heappush(self.queue, task)
        
        self.last_process_time = time.time()
    
    async def _dispatch_task(self, task: QueuedTask):
        """Mark a queued task as dispatched."""
        try:
            # Update task in dashboard (set is_queued=False)
            await self._update_task_queue_status(task.task_id, is_queued=False)
            logger.info(f"📤 Task '{task.title}' dispatched to dashboard")
        except Exception as e:
            logger.error(f"Failed to dispatch task {task.task_id}: {e}")
    
    async def _update_task_queue_status(self, task_id: int, is_queued: bool):
        """Update task queue status in dashboard using shared session."""
        url = f"{self.dashboard.api_url}/tasks/{task_id}/dispatch"
        
        if is_queued:
            # Mark as queued — task creation already handles is_queued flag
            pass
        else:
            # Dispatch task via dashboard client's shared session
            try:
                async with self.dashboard._get_session() as session:
                    async with session.put(url) as response:
                        if response.status == 200:
                            logger.debug(f"Task {task_id} dispatch status updated")
                        else:
                            logger.warning(f"Failed to update task {task_id}: {response.status}")
            except Exception as e:
                logger.error(f"Error updating task status: {e}")
    
    def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        if not self.queue:
            return {
                "total": 0,
                "by_urgency": {},
                "by_zone": {}
            }
        
        # Count by urgency
        by_urgency = {}
        by_zone = {}
        
        for task in self.queue:
            urgency_name = task.urgency.name
            by_urgency[urgency_name] = by_urgency.get(urgency_name, 0) + 1
            
            zone = task.zone or "general"
            by_zone[zone] = by_zone.get(zone, 0) + 1
        
        return {
            "total": len(self.queue),
            "by_urgency": by_urgency,
            "by_zone": by_zone
        }
