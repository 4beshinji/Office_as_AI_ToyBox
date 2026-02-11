import network
import time
import json
import machine
from umqtt.simple import MQTTClient

class MCPDevice:
    def __init__(self, device_id, ssid, password, broker, port=1883, topic_prefix=None):
        self.device_id = device_id
        self.ssid = ssid
        self.password = password
        self.broker = broker
        self.port = port
        self.topic_prefix = topic_prefix or f"office/sensor/{device_id}"
        self.client = None
        self.tools = {}

    def connect_wifi(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            print(f"Connecting to WiFi {self.ssid}...")
            wlan.connect(self.ssid, self.password)
            while not wlan.isconnected():
                time.sleep(1)
        print("WiFi connected:", wlan.ifconfig())

    def register_tool(self, name, callback):
        self.tools[name] = callback

    def _mqtt_callback(self, topic, msg):
        topic_str = topic.decode()
        print(f"Received message on {topic_str}")
        
        try:
            payload = json.loads(msg.decode())
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return

        if topic_str == f"mcp/{self.device_id}/request/call_tool":
            self._handle_tool_call(payload)

    def _handle_tool_call(self, payload):
        req_id = payload.get("id")
        method = payload.get("method")
        params = payload.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if method == "call_tool" and tool_name in self.tools:
            print(f"Executing tool: {tool_name}")
            try:
                result = self.tools[tool_name](**args)
                response = {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": req_id
                }
                self.client.publish(f"mcp/{self.device_id}/response/{req_id}", json.dumps(response))
            except Exception as e:
                print(f"Tool execution error: {e}")
                error_resp = {
                    "jsonrpc": "2.0",
                    "error": str(e),
                    "id": req_id
                }
                self.client.publish(f"mcp/{self.device_id}/response/{req_id}", json.dumps(error_resp))

    def connect(self):
        self.connect_wifi()
        self.client = MQTTClient(self.device_id, self.broker, port=self.port)
        self.client.set_callback(self._mqtt_callback)
        self.client.connect()
        self.client.subscribe(f"mcp/{self.device_id}/request/call_tool")
        print(f"Connected to MQTT Broker at {self.broker}")

    def loop(self):
        self.client.check_msg()

    def publish_telemetry(self, subtopic, data):
        topic = f"{self.topic_prefix}/{subtopic}"
        self.client.publish(topic, json.dumps(data))
        print(f"Published to {topic}: {data}")
