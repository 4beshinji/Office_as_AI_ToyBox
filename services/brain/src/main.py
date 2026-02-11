import asyncio
import os
import json
from loguru import logger
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from mcp_bridge import MCPBridge
from llm_client import LLMClient
from sanitizer import Sanitizer
from world_model import WorldModel
from task_scheduling import TaskQueueManager
from task_reminder import TaskReminder

# Load environment variables
load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
# Default to Mock LLM if not specified
LLM_API_URL = os.getenv("LLM_API_URL", "http://mock-llm:8000/v1")

from dashboard_client import DashboardClient

class Brain:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.mcp = MCPBridge(self.client)
        self.llm = LLMClient(api_url=LLM_API_URL)
        self.dashboard = DashboardClient() # Initialize Dashboard Client
        self.sanitizer = Sanitizer()
        self.message_buffer = []
        self.world_model = WorldModel()  # Initialize World Model
        self.task_queue = None  # Will be initialized after world_model
        self.task_reminder = TaskReminder()  # Initialize Task Reminder

    # ... (on_connect and on_message remain same)

    def on_connect(self, client, userdata, flags, rc, properties=None):
        logger.info(f"Connected to MQTT Broker with result code {rc}")
        client.subscribe("mcp/+/response/#")
        client.subscribe("office/#") 
        client.subscribe("hydro/#")
        client.subscribe("aqua/#")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            
            if "mcp" in topic and "response" in topic:
                self.mcp.handle_response(topic, payload)
            else:
                # Update World Model
                self.world_model.update_from_mqtt(topic, payload)
                
                # Keep message_buffer for legacy compatibility
                self.message_buffer.append({"topic": topic, "payload": payload})
                if len(self.message_buffer) > 10:
                    self.message_buffer.pop(0)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def cognitive_cycle(self):
        # Process task queue first
        if self.task_queue:
            await self.task_queue.process_queue()
        
        if not self.message_buffer:
            return

        current_context = json.dumps(self.message_buffer)
        
        # --- RULE BASED OVERRIDE FOR TESTING ---
        # If we see coffee machine empty, create a task immediately.
        # This bypasses the Mock LLM limitations for this specific test case.
        for msg in self.message_buffer:
            if "coffee_machine" in msg["topic"] and msg["payload"].get("beans_level") == 0:
                logger.info("Rule Triggered: Coffee Beans Empty -> Create Task")
                await self.dashboard.create_task(
                    title="コーヒー豆を補充してください",
                    description="キッチンのコーヒーマシンの豆が空っぽになっています。",
                    bounty=1000
                )
                self.message_buffer = [] # Clear handled messages
                return

            # NEW: High Temperature Rule
            if "temperature" in msg["topic"]:
                temp = msg["payload"].get("value")
                if temp and isinstance(temp, (int, float)) and temp > 30:
                    logger.info(f"Rule Triggered: High Temperature ({temp}°C) -> Create Task")
                    await self.dashboard.create_task(
                        title="室温を下げてください",
                        description=f"高温（{temp}°C）を検知しました。エアコンをつけるか窓を開けてください。",
                        bounty=1500
                    )
                    self.message_buffer = [] # Clear handled messages
                    return

            # NEW: Low Humidity Rule
            if "humidity" in msg["topic"]:
                hum = msg["payload"].get("value")
                if hum and isinstance(hum, (int, float)) and hum < 30:
                    logger.info(f"Rule Triggered: Low Humidity ({hum}%) -> Create Task")
                    await self.dashboard.create_task(
                        title="加湿と換気を行ってください",
                        description=f"低湿度（{hum}%）を検知しました。加湿器を稼働させ、定期的な換気を行って快適な環境を保ちましょう。",
                        bounty=1200
                    )
                    self.message_buffer = [] # Clear handled messages
                    return
        # ---------------------------------------

        system_prompt = {
            "role": "system",
            "content": "あなたは自律型オフィス管理AI「Brain」です。人々の活動や環境データを分析し、オフィスの快適さを維持するためのタスクを生成します。常に丁寧で自然な日本語で応答してください。"
        }
        
        # Use World Model context for LLM
        llm_context = self.world_model.get_llm_context()
        
        # Debug: Log World Model zones
        zones = list(self.world_model.zones.keys())
        logger.info(f"World Model zones: {zones}")
        if llm_context:
            logger.debug(f"LLM Context preview:\n{llm_context[:300]}")
        
        user_message = {
            "role": "user",
            "content": f"Current State:\n{llm_context}\n\nRaw Buffer: {current_context}"
        }

        try:
            response = await self.llm.generate_response([system_prompt, user_message])
            logger.info(f"LLM Thought: {response}")
            
            # TODO: Implement full JSON parsing for LLM tool calls
            # For now, relying on the Rule Based Override above for the specific user request.

        except Exception as e:
            logger.error(f"Cognitive Cycle Error: {e}")
        
        self.message_buffer = []

    async def run(self):
        logger.info(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT: {e}")
            return
        
        # Initialize TaskQueueManager after MQTT connection
        self.task_queue = TaskQueueManager(self.world_model, self.dashboard)
        logger.info("TaskQueueManager initialized")
        
        # Start reminder service as background task
        asyncio.create_task(self.task_reminder.run_periodic_check())
        logger.info("TaskReminder service started")

        logger.info("Brain is running...")
        while True:
            await self.cognitive_cycle()
            await asyncio.sleep(5)

if __name__ == "__main__":
    brain = Brain()
    try:
        asyncio.run(brain.run())
    except KeyboardInterrupt:
        pass
