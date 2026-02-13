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
from dashboard_client import DashboardClient
from tool_executor import ToolExecutor
from tool_registry import get_tools
from system_prompt import build_system_message

load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
LLM_API_URL = os.getenv("LLM_API_URL", "http://mock-llm:8000/v1")

REACT_MAX_ITERATIONS = 5
CYCLE_INTERVAL = 30       # Normal polling interval (seconds)
EVENT_BATCH_DELAY = 3     # Delay after event to batch multiple events (seconds)


class Brain:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.mcp = MCPBridge(self.client)
        self.llm = LLMClient(api_url=LLM_API_URL)
        self.dashboard = DashboardClient()
        self.sanitizer = Sanitizer()
        self.world_model = WorldModel()
        self.task_queue = None
        self.task_reminder = TaskReminder()
        self.tool_executor = None

        # Event-driven trigger
        self._cycle_triggered = asyncio.Event()
        self._last_event_count: dict[str, int] = {}

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
                self.world_model.update_from_mqtt(topic, payload)

                # Check if new events were generated -> trigger cycle
                current_event_counts = {
                    zid: len(z.events) for zid, z in self.world_model.zones.items()
                }
                if current_event_counts != self._last_event_count:
                    self._last_event_count = current_event_counts
                    self._cycle_triggered.set()

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def cognitive_cycle(self):
        """ReAct cognitive cycle: Think → Act → Observe → repeat."""
        # Process task queue
        if self.task_queue:
            await self.task_queue.process_queue()

        # Build context
        llm_context = self.world_model.get_llm_context()
        if not llm_context:
            return

        # Collect recent events (last 5 minutes)
        import time
        now = time.time()
        recent_events = []
        for zone_id, zone in self.world_model.zones.items():
            for event in zone.events:
                if now - event.timestamp < 300:
                    recent_events.append(f"[{zone_id}] {event.description}")

        # Fetch active tasks to prevent duplicates
        active_tasks = await self.dashboard.get_active_tasks()

        # Build messages
        system_msg = build_system_message()
        user_content = f"## 現在のオフィス状態\n{llm_context}"
        if recent_events:
            user_content += f"\n\n## 直近のイベント\n" + "\n".join(recent_events)

        # Inject active tasks so LLM knows what already exists
        if active_tasks:
            user_content += "\n\n## 現在のアクティブタスク（重複作成禁止）\n"
            for t in active_tasks[:10]:
                title = t.get("title", "")
                zone = t.get("zone", "")
                task_type = t.get("task_type", [])
                zone_str = f" [{zone}]" if zone else ""
                type_str = f" ({','.join(task_type)})" if task_type else ""
                user_content += f"- {title}{zone_str}{type_str}\n"
            user_content += "上記タスクと同じ目的のタスクを新規作成しないでください。"
        else:
            user_content += "\n\n## 現在のアクティブタスク\nなし"

        user_msg = {"role": "user", "content": user_content}

        messages = [system_msg, user_msg]
        tools = get_tools()

        # ReAct loop
        for iteration in range(1, REACT_MAX_ITERATIONS + 1):
            logger.info(f"ReAct iteration {iteration}/{REACT_MAX_ITERATIONS}")

            response = await self.llm.chat(messages, tools)

            if response.error:
                logger.error(f"LLM error: {response.error}")
                break

            # No tool calls -> LLM decided no action needed
            if not response.tool_calls:
                if response.content:
                    logger.info(f"LLM (no action): {response.content[:200]}")
                break

            # Process tool calls
            # Add assistant message with tool_calls to conversation
            assistant_msg = {"role": "assistant", "content": response.content or ""}
            assistant_msg["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["function"]["name"],
                        "arguments": json.dumps(tc["function"]["arguments"], ensure_ascii=False),
                    }
                }
                for tc in response.tool_calls
            ]
            messages.append(assistant_msg)

            # Execute each tool call
            for tc in response.tool_calls:
                tool_name = tc["function"]["name"]
                arguments = tc["function"]["arguments"]
                tool_call_id = tc["id"]

                logger.info(f"Executing tool: {tool_name} with {arguments}")

                result = await self.tool_executor.execute(tool_name, arguments)

                if result["success"]:
                    logger.info(f"Tool result: {result['result'][:200]}")
                else:
                    logger.warning(f"Tool failed: {result['error']}")

                # Add tool result to conversation
                result_content = result.get("result") or result.get("error", "")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": str(result_content),
                })

            # Continue loop - LLM will see tool results and decide next action

        logger.info("Cycle complete.")

    async def run(self):
        logger.info(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT: {e}")
            return

        # Initialize components
        self.task_queue = TaskQueueManager(self.world_model, self.dashboard)
        self.tool_executor = ToolExecutor(
            sanitizer=self.sanitizer,
            mcp_bridge=self.mcp,
            dashboard_client=self.dashboard,
            world_model=self.world_model,
            task_queue=self.task_queue,
        )
        logger.info("TaskQueueManager and ToolExecutor initialized")

        # Start reminder service
        asyncio.create_task(self.task_reminder.run_periodic_check())
        logger.info("TaskReminder service started")

        logger.info("Brain is running (ReAct mode)...")
        while True:
            # Wait for event trigger or timeout
            try:
                await asyncio.wait_for(
                    self._cycle_triggered.wait(),
                    timeout=CYCLE_INTERVAL,
                )
                # Event triggered - wait briefly to batch multiple events
                self._cycle_triggered.clear()
                await asyncio.sleep(EVENT_BATCH_DELAY)
            except asyncio.TimeoutError:
                pass  # Normal polling interval reached

            try:
                await self.cognitive_cycle()
            except Exception as e:
                logger.error(f"Cognitive cycle error: {e}")


if __name__ == "__main__":
    brain = Brain()
    try:
        asyncio.run(brain.run())
    except KeyboardInterrupt:
        pass
