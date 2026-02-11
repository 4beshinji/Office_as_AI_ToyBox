"""
Vision/Perception Service
MQTT-based multi-task monitoring system with YOLOv11
"""
import asyncio
import logging
import yaml
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import components
from scheduler import TaskScheduler
from monitors import OccupancyMonitor, WhiteboardMonitor
from image_requester import ImageRequester
from yolo_inference import YOLOInference
from state_publisher import StatePublisher

async def main():
    logger.info("=== Vision Service Starting ===")
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "monitors.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Initialize shared components
    mqtt_config = config.get("mqtt", {})
    broker = mqtt_config.get("broker", "localhost")
    port = mqtt_config.get("port", 1883)
    
    logger.info(f"MQTT Broker: {broker}:{port}")
    
    # Initialize singletons
    ImageRequester.get_instance(broker, port)
    StatePublisher.get_instance(broker, port)
    
    # Load YOLO model
    yolo_config = config.get("yolo", {})
    model_path = yolo_config.get("model", "yolov11s.pt")
    YOLOInference.get_instance(model_path)
    
    # Create scheduler
    scheduler = TaskScheduler()
    
    # Register monitors
    for monitor_config in config.get("monitors", []):
        if not monitor_config.get("enabled", True):
            logger.info(f"Skipping disabled monitor: {monitor_config['name']}")
            continue
            
        monitor_type = monitor_config["type"]
        camera_id = monitor_config["camera_id"]
        zone_name = monitor_config.get("zone_name", "default")
        
        if monitor_type == "OccupancyMonitor":
            monitor = OccupancyMonitor(camera_id, zone_name)
        elif monitor_type == "WhiteboardMonitor":
            monitor = WhiteboardMonitor(camera_id, zone_name)
        else:
            logger.warning(f"Unknown monitor type: {monitor_type}")
            continue
            
        scheduler.register_monitor(monitor_config["name"], monitor)
    
    logger.info("=== Vision Service Ready ===")
    
    # Start monitoring
    await scheduler.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
