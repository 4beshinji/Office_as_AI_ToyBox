
from typing import Dict, Any, List
from loguru import logger

class Sanitizer:
    def __init__(self):
        # Hardcoded safety limits
        self.safety_limits = {
            "set_temperature": {"min": 18, "max": 28},
            "pump_duration": {"max": 60}, # seconds
        }
        # In a real system, this would be loaded from inventory.yaml
        self.allowed_devices = ["light_01", "pump_01", "window_01"]

    def validate_tool_call(self, tool_name: str, args: Dict[str, Any]) -> bool:
        """
        Returns True if the tool call is safe, False otherwise.
        """
        logger.info(f"Sanitizing: {tool_name} with {args}")

        # 1. Device Existence Check
        if "device_id" in args:
            if args["device_id"] not in self.allowed_devices:
                logger.warning(f"REJECTED: Unknown device {args['device_id']}")
                return False

        # 2. Parameter Limit Check
        if tool_name == "set_temperature":
            temp = args.get("temperature")
            if temp is not None:
                if not (self.safety_limits["set_temperature"]["min"] <= temp <= self.safety_limits["set_temperature"]["max"]):
                    logger.warning(f"REJECTED: Temperature {temp} out of bounds")
                    return False
        
        if tool_name == "run_pump":
            duration = args.get("duration")
            if duration is not None:
                if duration > self.safety_limits["pump_duration"]["max"]:
                    logger.warning(f"REJECTED: Pump duration {duration} exceeds limit")
                    return False

        return True
