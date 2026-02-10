import aiohttp
import os
import json
from loguru import logger

class DashboardClient:
    def __init__(self, api_url=None):
        # Default to internal docker-compose DNS name for backend
        self.api_url = api_url or os.getenv("DASHBOARD_API_URL", "http://backend:8000")
    
    async def create_task(self, title: str, description: str, bounty: int = 0):
        url = f"{self.api_url}/tasks/"
        params = {
            "title": title,
            "description": description,
            "bounty": bounty
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
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
