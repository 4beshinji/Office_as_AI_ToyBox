
import time
from typing import Dict, Any, Tuple
from loguru import logger


class Sanitizer:
    def __init__(self):
        self.safety_limits = {
            "set_temperature": {"min": 18, "max": 28},
            "pump_duration": {"max": 60},
        }
        self.allowed_devices = ["light_01", "pump_01", "window_01"]

        # Rate limiting for task creation
        self._task_creation_times: list[float] = []
        self._max_tasks_per_hour = 10

    def validate_tool_call(self, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a tool call. Returns (is_safe, reason).
        """
        logger.info(f"Sanitizing: {tool_name} with {args}")

        if tool_name == "create_task":
            return self._validate_create_task(args)
        elif tool_name == "send_device_command":
            return self._validate_device_command(args)
        elif tool_name in ("get_zone_status", "get_active_tasks"):
            return True, "Query tools are always allowed"
        else:
            logger.warning(f"REJECTED: Unknown tool {tool_name}")
            return False, f"Unknown tool: {tool_name}"

    def _validate_create_task(self, args: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate create_task parameters."""
        # Bounty cap
        bounty = args.get("bounty", 0)
        if isinstance(bounty, (int, float)) and bounty > 5000:
            logger.warning(f"REJECTED: Bounty {bounty} exceeds maximum 5000")
            return False, f"Bounty {bounty} exceeds maximum of 5000"

        # Urgency range
        urgency = args.get("urgency", 2)
        if isinstance(urgency, (int, float)) and not (0 <= urgency <= 4):
            logger.warning(f"REJECTED: Urgency {urgency} out of range 0-4")
            return False, f"Urgency {urgency} must be between 0 and 4"

        # Rate limiting
        now = time.time()
        self._task_creation_times = [
            t for t in self._task_creation_times
            if now - t < 3600
        ]
        if len(self._task_creation_times) >= self._max_tasks_per_hour:
            logger.warning(f"REJECTED: Rate limit exceeded ({self._max_tasks_per_hour} tasks/hour)")
            return False, f"Rate limit exceeded: {self._max_tasks_per_hour} tasks per hour"

        # Record this creation time (will be confirmed on successful execution)
        self._task_creation_times.append(now)

        return True, "OK"

    def _validate_device_command(self, args: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate send_device_command parameters."""
        # Device existence check
        agent_id = args.get("agent_id", "")
        tool_name = args.get("tool_name", "")

        # Parse nested arguments if string
        inner_args = args.get("arguments", {})
        if isinstance(inner_args, str):
            import json
            try:
                inner_args = json.loads(inner_args)
            except (json.JSONDecodeError, TypeError):
                inner_args = {}

        # Temperature range check
        if tool_name == "set_temperature":
            temp = inner_args.get("temperature")
            if temp is not None:
                limits = self.safety_limits["set_temperature"]
                if not (limits["min"] <= temp <= limits["max"]):
                    logger.warning(f"REJECTED: Temperature {temp} out of bounds [{limits['min']}-{limits['max']}]")
                    return False, f"Temperature {temp}°C out of safe range [{limits['min']}-{limits['max']}°C]"

        # Pump duration check
        if tool_name == "run_pump":
            duration = inner_args.get("duration")
            if duration is not None:
                if duration > self.safety_limits["pump_duration"]["max"]:
                    logger.warning(f"REJECTED: Pump duration {duration} exceeds limit")
                    return False, f"Pump duration {duration}s exceeds maximum {self.safety_limits['pump_duration']['max']}s"

        return True, "OK"
