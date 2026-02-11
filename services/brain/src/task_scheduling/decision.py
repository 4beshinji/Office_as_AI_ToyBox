"""
Task dispatch decision logic.
Determines whether a task should be dispatched immediately or queued.
"""
from typing import Optional
from loguru import logger
import time


class TaskDispatchDecision:
    """
    Decides when to dispatch tasks based on context.
    """
    
    def __init__(self, world_model):
        self.world_model = world_model
    
    def should_dispatch_now(
        self,
        urgency: int,
        zone: Optional[str],
        min_people_required: int,
        interruptible: bool = True
    ) -> tuple[bool, str]:
        """
        Determine if a task should be dispatched immediately.
        
        Args:
            urgency: Task urgency (0-4)
            zone: Target zone ID
            min_people_required: Minimum people needed
            interruptible: Whether the task can interrupt focused work
        
        Returns:
            (should_dispatch, reason) tuple
        """
        
        # Rule 1: CRITICAL tasks always dispatch immediately
        if urgency >= 4:
            return True, "Critical urgency"
        
        # Rule 2: If no zone specified, dispatch immediately (general task)
        if not zone:
            return True, "No zone constraint"
        
        # Get zone state from World Model
        zone_state = self.world_model.get_zone(zone)
        
        # Rule 3: If zone doesn't exist yet, queue it (wait for zone to be active)
        if not zone_state:
            return False, f"Zone '{zone}' not active yet"
        
        # Rule 4: Check minimum people requirement
        if zone_state.occupancy.person_count < min_people_required:
            return False, f"Not enough people in {zone} ({zone_state.occupancy.person_count}/{min_people_required})"
        
        # Rule 5: Avoid interrupting focused users (unless urgent)
        if not interruptible and urgency < 3:
            dominant_activity = zone_state.occupancy.dominant_activity
            if "focused" in dominant_activity.lower():
                return False, f"Users in {zone} are focused (non-interruptible task)"
        
        # Rule 6: Prefer dispatching during active hours
        current_hour = time.localtime().tm_hour
        if current_hour < 7 or current_hour > 22:
            if urgency < 3:
                return False, "Outside preferred hours (7:00-22:00)"
        
        # Rule 7: If high urgency, dispatch regardless of activity
        if urgency >= 3:
            return True, f"High urgency ({urgency})"
        
        # Default: Dispatch if people are present and active
        if zone_state.occupancy.person_count > 0:
            return True, f"Zone {zone} occupied ({zone_state.occupancy.person_count} people)"
        
        # Queue if zone is empty
        return False, f"Zone {zone} is empty"
    
    def get_optimal_dispatch_conditions(
        self,
        urgency: int,
        zone: Optional[str],
        min_people_required: int
    ) -> str:
        """
        Generate human-readable optimal dispatch conditions.
        Used for logging/debugging.
        """
        conditions = []
        
        if urgency >= 4:
            return "Immediate dispatch (CRITICAL)"
        
        if zone:
            conditions.append(f"Zone '{zone}' active")
            if min_people_required > 1:
                conditions.append(f"At least {min_people_required} people present")
        
        if urgency < 3:
            conditions.append("Users not in focused state")
            conditions.append("During active hours (7:00-22:00)")
        
        return " AND ".join(conditions) if conditions else "Anytime"
