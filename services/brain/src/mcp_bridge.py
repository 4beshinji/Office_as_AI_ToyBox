
import asyncio
import json
import uuid
from typing import Dict, Any, Callable, Awaitable

class MCPBridge:
    def __init__(self, mqtt_client):
        self.mqtt_client = mqtt_client
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.tools: Dict[str, Dict[str, Any]] = {}

    async def call_tool(self, agent_id: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        topic = f"mcp/{agent_id}/request/call_tool"
        
        payload = {
            "jsonrpc": "2.0",
            "method": "call_tool",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": request_id
        }
        
        # Create a Future to await response
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_requests[request_id] = future
        
        # Publish request
        self.mqtt_client.publish(topic, json.dumps(payload))
        
        try:
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=10.0)
            return response
        except asyncio.TimeoutError:
            del self.pending_requests[request_id]
            raise TimeoutError(f"Tool execution timed out: {tool_name} on {agent_id}")

    def handle_response(self, topic: str, payload: Dict[str, Any]):
        # Expected topic: mcp/{agent_id}/response/{request_id}
        parts = topic.split('/')
        if len(parts) < 4:
            return
            
        request_id = parts[3] # Extract ID from topic or payload? 
        # Actually payload should contain ID as per JSON-RPC
        if "id" in payload:
            request_id = payload["id"]
            
        if request_id in self.pending_requests:
            future = self.pending_requests[request_id]
            if not future.done():
                if "error" in payload:
                     future.set_exception(Exception(payload["error"]))
                else:
                     future.set_result(payload.get("result"))
            del self.pending_requests[request_id]
