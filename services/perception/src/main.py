import os
import cv2
import json
import time
from ultralytics import YOLO
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
RTSP_URL = os.getenv("RTSP_URL", "0") # Default to webcam 0

class PerceptionNode:
    def __init__(self):
        self.model = YOLO("yolov8n.pt") # Using Nano for speed/example
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        
    def connect_mqtt(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            print("Connected to MQTT")
        except Exception as e:
            print(f"MQTT Connection Failed: {e}")

    def run(self):
        self.connect_mqtt()
        cap = cv2.VideoCapture(RTSP_URL)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                time.sleep(5)
                # Reconnect logic should be here
                cap = cv2.VideoCapture(RTSP_URL) 
                continue

            # Run inference
            results = self.model(frame, verbose=False)
            
            # Process results
            # For "Person" detection
            detections = []
            for r in results:
                for box in r.boxes:
                    cls = int(box.cls[0])
                    if self.model.names[cls] == "person":
                        conf = float(box.conf[0])
                        if conf > 0.5:
                            detections.append({"class": "person", "conf": conf, "box": box.xyxy[0].tolist()})

            if detections:
                payload = {
                    "timestamp": time.time(),
                    "count": len(detections),
                    "detections": detections
                }
                # Publish detailed detections
                self.client.publish("office/vision/cam_01/detections", json.dumps(payload))
                
                # Simple Occupancy Boolean
                self.client.publish("office/vision/cam_01/occupancy", "true")
            else:
                self.client.publish("office/vision/cam_01/occupancy", "false")

            # Throttle to 1 FPS to save bandwidth/compute
            time.sleep(1.0)

if __name__ == "__main__":
    node = PerceptionNode()
    node.run()
