import aiohttp
import os
import json
from loguru import logger

class DashboardClient:
    def __init__(self, api_url=None):
        # Default to internal docker-compose DNS name for backend
        self.api_url = api_url or os.getenv("DASHBOARD_API_URL", "http://backend:8000")
    
    async def create_task(self, title: str, description: str, bounty: int = 0, task_types: list[str] = None, expires_in_minutes: int = None):
        """
        Create a new task in the dashboard.
        
        Args:
            title: Task title
            description: Task description
            bounty: Reward amounts (Jinbo Points)
            task_types: List of task types (e.g., ['supply', 'urgent'])
            expires_in_minutes: Duration content should be displayed (minutes). If None, calculated based on types.
        """
        from datetime import datetime, timedelta, timezone

        if task_types is None:
            task_types = ["general"]

        # Determine expiration if not provided
        if expires_in_minutes is None:
            expires_in_minutes = 60 * 24 # Default 24h
            
            # Application specific rules
            if 'environment' in task_types: # e.g. lights on
                expires_in_minutes = min(expires_in_minutes, 60) # 1 hour max for env issues
            if 'supply' in task_types:
                expires_in_minutes = 60 * 24 * 7 # 1 week for supplies
            if 'urgent' in task_types:
                expires_in_minutes = min(expires_in_minutes, 30) # 30 mins for urgent

        # Calculate expires_at
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)).isoformat()

        url = f"{self.api_url}/tasks/"
        payload = {
            "title": title,
            "description": description,
            "bounty_gold": bounty,
            "task_type": task_types,
            "expires_at": expires_at,
            "location": "Office"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Task created successfully: {data}")
                        return data
                    else:
                        logger.error(f"Failed to create task: {response.status} {await response.text()}")
                        return None
        except Exception as e:
            logger.error(f"Error communicating with Dashboard API: {e}")
            return None
