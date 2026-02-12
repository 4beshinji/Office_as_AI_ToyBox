import time
import asyncio
from typing import Dict, Optional
from loguru import logger

class ActivityMonitor:
    """
    Monitors user activity levels in zones and triggers health interventions.
    """
    def __init__(self, world_model, dashboard_client):
        self.world_model = world_model
        self.dashboard = dashboard_client
        self.last_check = time.time()
        
        # Track how long a zone has been "sedentary"
        # key: zone_id, value: timestamp when sedentary state started
        self.sedentary_start_times: Dict[str, float] = {}
        
        # Configuration
        self.check_interval = 60 # Check every minute
        import os
        self.sedentary_threshold_minutes = float(os.getenv("SEDENTARY_THRESHOLD_MINUTES", 30)) # Configurable check
        self.motion_threshold = 0.1 # Below this is considered sedentary
        
        # CD (Cooldown) to avoid spamming voice
        self.last_alert_times: Dict[str, float] = {}
        self.alert_cooldown = 3600 # 1 hour cooldown per zone

    async def check_activity(self):
        """Run periodic check."""
        current_time = time.time()
        
        for zone_id, zone in self.world_model.zones.items():
            # Skip if no one is there
            if zone.occupancy.person_count == 0:
                if zone_id in self.sedentary_start_times:
                    del self.sedentary_start_times[zone_id]
                continue
            
            # Check motion level
            avg_motion = zone.occupancy.avg_motion_level
            
            if avg_motion < self.motion_threshold:
                # Sedentary state
                if zone_id not in self.sedentary_start_times:
                    self.sedentary_start_times[zone_id] = current_time
                    logger.debug(f"Zone {zone_id} entered sedentary state.")
                
                # Check duration
                duration = current_time - self.sedentary_start_times[zone_id]
                if duration > (self.sedentary_threshold_minutes * 60):
                    await self._trigger_sedentary_alert(zone_id)
            else:
                # Active state - reset timer
                if zone_id in self.sedentary_start_times:
                    logger.debug(f"Zone {zone_id} broke sedentary state (Motion: {avg_motion}).")
                    del self.sedentary_start_times[zone_id]

    async def _trigger_sedentary_alert(self, zone_id: str):
        """Trigger a voice-only task for health advice."""
        current_time = time.time()
        
        # Check cooldown
        last_alert = self.last_alert_times.get(zone_id, 0)
        if (current_time - last_alert) < self.alert_cooldown:
            return

        logger.info(f"Triggering Sedentary Alert for {zone_id}")
        
        try:
            # Create "Voice Only" task
            await self.dashboard.create_task(
                title="健康アドバイス",
                description="長時間座りっぱなしのようです。少し背伸びをしたり、水分補給をしてリフレッシュしませんか？",
                bounty=0, # No bounty for advice
                task_types=["voice_only", "health"],
                expires_in_minutes=5, # Short life
                urgency=1,
                zone=zone_id,
                announce=True
            )
            
            self.last_alert_times[zone_id] = current_time
            # Reset sedentary timer to avoid repeated alerts immediately? 
            # Or keep it and let cooldown handle it. Cooldown is safer.
            
        except Exception as e:
            logger.error(f"Failed to trigger sedentary alert: {e}")
