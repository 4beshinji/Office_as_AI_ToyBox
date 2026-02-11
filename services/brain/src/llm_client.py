
import os
import json
import aiohttp
from typing import List, Dict, Any, Optional

class LLMClient:
    def __init__(self, api_url: str = "http://localhost:8000/v1"):
        self.api_url = api_url
        self.api_key = os.getenv("OPENAI_API_KEY", "EMPTY")
        self.model = os.getenv("LLM_MODEL", "qwen2.5:14b")
        
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates a response from the LLM, optionally constrained by tools or schema.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
        }

        # If tools are provided, format them for the model
        # Note: Qwen2.5 supports tool calling via specific prompt formats or API
        if tools:
            # For simplicity in this initial implementation, we might inject tools into system prompt
            # or use the OpenAI-compatible 'tools' parameter if vLLM supports it fully.
            # vLLM's tool support is evolving.
            pass 

        # If schema is provided (for Guided Generation)
        if schema:
            payload["guided_json"] = schema

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.api_url}/chat/completions", headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"LLM API Error {resp.status}: {error_text}")
                    
                    return await resp.json()
            except Exception as e:
                print(f"LLM Connection Error: {e}")
                return {"error": str(e)}

