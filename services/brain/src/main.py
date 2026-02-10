import asyncio
import os
import json
from loguru import logger
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from mcp_bridge import MCPBridge
from llm_client import LLMClient
from sanitizer import Sanitizer

# Load environment variables
load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:8000/v1")

class Brain:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.mcp = MCPBridge(self.client)
        self.llm = LLMClient(api_url=LLM_API_URL)
        self.sanitizer = Sanitizer()
        self.message_buffer = [] # Store incoming sensor data for context

    def on_connect(self, client, userdata, flags, rc, properties=None):
        logger.info(f"Connected to MQTT Broker with result code {rc}")
        # Subscribe to all MCP responses and Sensor data
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
                # Store latest sensor data
                # Simplified: Just keep the last 10 messages for now
                self.message_buffer.append({"topic": topic, "payload": payload})
                if len(self.message_buffer) > 10:
                    self.message_buffer.pop(0)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def cognitive_cycle(self):
        """
        The main thinking loop.
        1. Analyze current state (from message_buffer).
        2. Decide on action (LLM).
        3. Execute action (MCP + Sanitizer).
        """
        if not self.message_buffer:
            return

        # Simple Trigger: If we have new messages, let's "think"
        # In production, this should be more sophisticated (e.g., specific triggers or timer)
        
        current_context = json.dumps(self.message_buffer)
        
        system_prompt = {
            "role": "system",
            "content": "You are the Autonomous Office Manager. You monitor the office state via MQTT messages. "
                       "If you see a problem (e.g. temp too high), call the appropriate tool. "
                       "If everything is fine, just say 'Status Normal'."
        }
        
        user_message = {
            "role": "user",
            "content": f"Current State: {current_context}"
        }

        # Call LLM
        try:
            # We would pass available tools definition here
            # For now, let's assume the LLM just returns text or a JSON with tool_calls
            response = await self.llm.generate_response([system_prompt, user_message])
            logger.info(f"LLM Thought: {response}")
            
            # Mock parsing logic (Real implementation needs robust JSON parsing)
            # if response has tool_calls:
            #   for tool in tools:
            #     if self.sanitizer.validate_tool_call(tool.name, tool.args):
            #       self.mcp.call_tool(tool.agent_id, tool.name, tool.args)
    
        except Exception as e:
            logger.error(f"Cognitive Cycle Error: {e}")
        
        # Clear buffer after processing
        self.message_buffer = []

    async def run(self):
        logger.info(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT: {e}")
            return

        # Main Event Loop
        logger.info("Brain is running...")
        while True:
            await self.cognitive_cycle()
            await asyncio.sleep(5) # Think every 5 seconds

if __name__ == "__main__":
    brain = Brain()
    try:
        asyncio.run(brain.run())
    except KeyboardInterrupt:
        pass
