import sys
import os
import time
import json
import requests
import paho.mqtt.client as mqtt
from loguru import logger

# Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
DASHBOARD_API = os.getenv("DASHBOARD_API", "http://localhost:8000")

def on_connect(client, userdata, flags, rc, properties=None):
    logger.info(f"Connected to MQTT with result code {rc}")

def run_test():
    logger.info("--- Starting Voice Interaction Test ---")
    
    # 1. Setup MQTT
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    
    time.sleep(1)
    
    # 2. Simulate Sedentary Behavior
    # We need to send updates for > 30 mins (simulated time?)
    # The ActivityMonitor uses real time (time.time()), so testing 30 mins wait is too long.
    # WE NEED TO PATCH THE MONITOR OR USE A SPECIAL TEST MODE IN BRAIN.
    # OR: We can manually update the `sedentary_start_times` in the Brain? No, isolated container.
    # IDEA: Trigger a debug topic that forces the check?
    # BETTER IDEA: Just update the `activity_monitor.py` to use a shorter threshold if env var is set?
    
    # Let's assume we patched it or we wait if we can't patch.
    # Wait, I can patch the file in the container easily.
    
    logger.info("Injecting Sedentary Data...")
    zone = "office_test_zone"
    
    # Send "Person Present" but "Low Motion"
    payload = {
        "person_count": 1,
        "avg_motion_level": 0.05,
        "activity_distribution": {"focused": 100}
    }
    client.publish(f"office/{zone}/camera/occupancy", json.dumps(payload))
    
    # We need to simulate time passing.
    # Since we can't control time.time() inside the container easily without mocking,
    # I will rely on a "TEST_MODE" patch I will apply to `activity_monitor.py` 
    # that sets threshold to 5 seconds.
    
    logger.info("Waiting for Sedentary Alert threshold...")
    for i in range(10):
        client.publish(f"office/{zone}/camera/occupancy", json.dumps(payload))
        time.sleep(1) 
    
    # 3. Check Dashboard for "voice_only" task
    logger.info("Checking Dashboard for Voice Task...")
    try:
        resp = requests.get(f"{DASHBOARD_API}/tasks/")
        tasks = resp.json()
        logger.info(f"Tasks response: {tasks}")
        
        if not isinstance(tasks, list):
            logger.error(f"Expected list, got {type(tasks)}")
            sys.exit(1)
            
        found = False
        for t in tasks:
            if t.get("zone") == zone and "voice_only" in (t.get("task_type") or []):
                found = True
                logger.success(f"✅ Voice Task Found: {t['title']}")
                logger.info(f"Audio URL: {t.get('announcement_audio_url')}")
                break
        
        if not found:
            logger.error("❌ Voice Task NOT Found")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to check dashboard: {e}")
        sys.exit(1)

    logger.success("--- Test Passed ---")
    client.loop_stop()

if __name__ == "__main__":
    run_test()
