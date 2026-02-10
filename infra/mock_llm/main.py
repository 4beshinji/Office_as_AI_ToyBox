from fastapi import FastAPI, Request
import json

app = FastAPI()

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    
    # Simple Keyword Logic
    # 1. Flatten messages to search for keywords
    full_text = " ".join([m.get("content", "") for m in messages]).lower()
    
    content = "Status Normal."
    tool_calls = None

    if "temperature" in full_text and "high" in full_text:
        content = "Temperature is too high. Turning on AC."
        # Hypothetical Tool Call Format (OpenAI style)
        # Note: In our Brain implementation, we might parse JSON from content
        # or use structured outputs. Let's assume Brain parses JSON from text for now.
        content = json.dumps({
            "thought": "Temperature is high triggered by sensor data.",
            "action": "call_tool",
            "tool_name": "turn_on_ac",
            "arguments": {"temp": 24}
        })
    elif "ph" in full_text and "high" in full_text:
        content = json.dumps({
            "thought": "pH is high. Dosing pH Down.",
            "action": "call_tool",
            "tool_name": "dose_ph_down",
            "arguments": {"amount_ml": 5}
        })

    return {
        "id": "mock-response-id",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "mock-qwen",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content,
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 10,
            "total_tokens": 20
        }
    }
