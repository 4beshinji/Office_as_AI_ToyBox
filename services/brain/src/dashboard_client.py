import aiohttp
import os
import json
from loguru import logger

class DashboardClient:
    def __init__(self, api_url=None, voice_url=None, enable_voice=True):
        # Default to internal docker-compose DNS name for backend
        self.api_url = api_url or os.getenv("DASHBOARD_API_URL", "http://backend:8000")
        self.voice_url = voice_url or os.getenv("VOICE_SERVICE_URL", "http://voice-service:8000")
        self.enable_voice = enable_voice
    
    async def create_task(
        self, 
        title: str, 
        description: str, 
        bounty: int = 0, 
        task_types: list[str] = None, 
        expires_in_minutes: int = None,
        urgency: int = 2,
        zone: str = None,
        announce: bool = None
    ):
        """
        Create a new task in the dashboard.
        
        Args:
            title: Task title
            description: Task description
            bounty: Reward amounts (Jinbo Points)
            task_types: List of task types (e.g., ['supply', 'urgent'])
            expires_in_minutes: Duration content should be displayed (minutes). If None, calculated based on types.
            urgency: Task urgency level (0-4)
            zone: Task location zone
            announce: Whether to announce via voice (default: True if voice enabled)
        """
        from datetime import datetime, timedelta, timezone

        if task_types is None:
            task_types = ["general"]
        
        if announce is None:
            announce = self.enable_voice

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
            "location": "Office",
            "urgency": urgency,
            "zone": zone
        }
        
        # Generate dual voice if enabled (before task creation)
        voice_data = None
        if announce:
            try:
                voice_data = await self._generate_dual_voice({
                    "title": title,
                    "description": description,
                    "location": "Office",
                    "bounty_gold": bounty,
                    "urgency": urgency,
                    "zone": zone
                })
                # Add voice data to payload
                if voice_data:
                    payload["announcement_audio_url"] = voice_data["announcement_audio_url"]
                    payload["announcement_text"] = voice_data["announcement_text"]
                    payload["completion_audio_url"] = voice_data["completion_audio_url"]
                    payload["completion_text"] = voice_data["completion_text"]
            except Exception as e:
                logger.warning(f"Failed to generate dual voice: {e}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Task created successfully: {data}")
                        
                        # Note: Voice was already generated and stored in task
                        if voice_data:
                            logger.info(f"Announcement: {voice_data['announcement_text']}")
                            logger.info(f"Completion: {voice_data['completion_text']}")
                        
                        return data
                    else:
                        logger.error(f"Failed to create task: {response.status} {await response.text()}")
                        return None
        except Exception as e:
            logger.error(f"Error communicating with Dashboard API: {e}")
            return None
    
    async def _generate_dual_voice(self, task_data: dict) -> dict:
        """
        Call voice service to generate both announcement and completion voices.
        
        Args:
            task_data: Task data
        
        Returns:
            Dict with announcement and completion audio URLs and texts
        """
        try:
            url = f"{self.voice_url}/api/voice/announce_with_completion"
            payload = {
                "task": task_data
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        logger.info(f"Dual voice generated successfully")
                        return result
                    else:
                        logger.warning(f"Dual voice generation failed: {resp.status}")
                        return None
                        
        except Exception as e:
            logger.warning(f"Failed to generate dual voice: {e}")
            return None
