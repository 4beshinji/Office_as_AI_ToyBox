from fastapi import FastAPI, Request
import json
import uuid

app = FastAPI()


def _make_tool_call(name: str, arguments: dict) -> dict:
    """Helper to build an OpenAI-format tool_call."""
    return {
        "id": f"call_{uuid.uuid4().hex[:8]}",
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(arguments, ensure_ascii=False),
        }
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    tools = body.get("tools", [])

    # Check if this is a follow-up with tool results
    has_tool_results = any(m.get("role") == "tool" for m in messages)
    if has_tool_results:
        # Tool results received -> respond with completion text
        return _response(content="対応を実行しました。状況を引き続き監視します。")

    # Flatten messages for keyword matching
    full_text = " ".join([m.get("content", "") or "" for m in messages]).lower()

    # High temperature detection
    if ("温度" in full_text or "気温" in full_text or "temperature" in full_text) and (
        "高" in full_text or "hot" in full_text or "暑" in full_text or "30" in full_text
    ):
        return _response(
            content="高温を検知しました。タスクを作成します。",
            tool_calls=[
                _make_tool_call("create_task", {
                    "title": "室温を下げてください",
                    "description": "高温を検知しました。エアコンをつけるか窓を開けて室温を下げてください。",
                    "bounty": 1500,
                    "urgency": 3,
                    "task_types": "environment,urgent",
                })
            ]
        )

    # High CO2 detection
    if ("co2" in full_text or "二酸化炭素" in full_text) and (
        "換気" in full_text or "1000" in full_text or "超" in full_text
    ):
        return _response(
            content="CO2濃度が高いです。換気タスクを作成します。",
            tool_calls=[
                _make_tool_call("create_task", {
                    "title": "換気を行ってください",
                    "description": "CO2濃度が基準値を超えています。窓を開けて換気してください。",
                    "bounty": 800,
                    "urgency": 2,
                    "task_types": "environment",
                })
            ]
        )

    # Coffee beans empty
    if "コーヒー" in full_text and ("空" in full_text or "補充" in full_text or "0" in full_text):
        return _response(
            content="コーヒー豆が空です。補充タスクを作成します。",
            tool_calls=[
                _make_tool_call("create_task", {
                    "title": "コーヒー豆を補充してください",
                    "description": "キッチンのコーヒーマシンの豆が空です。補充をお願いします。",
                    "bounty": 1000,
                    "urgency": 1,
                    "task_types": "supply",
                })
            ]
        )

    # Low humidity
    if ("湿度" in full_text or "humidity" in full_text) and (
        "低" in full_text or "乾燥" in full_text
    ):
        return _response(
            content="低湿度を検知しました。加湿タスクを作成します。",
            tool_calls=[
                _make_tool_call("create_task", {
                    "title": "加湿と換気を行ってください",
                    "description": "低湿度を検知しました。加湿器を稼働させて快適な環境を保ちましょう。",
                    "bounty": 1200,
                    "urgency": 2,
                    "task_types": "environment",
                })
            ]
        )

    # Sedentary alert -> speak with caring tone
    if "sedentary_alert" in full_text or "座り" in full_text or "姿勢" in full_text:
        return _response(
            content="長時間座り続けている方がいます。声をかけます。",
            tool_calls=[
                _make_tool_call("speak", {
                    "message": "ずっと座りっぱなしみたいですね。少し立ち上がってストレッチしませんか？",
                    "tone": "caring",
                })
            ]
        )

    # Sensor tamper -> speak with humorous tone
    if "sensor_tamper" in full_text or "急変" in full_text or "いたずら" in full_text:
        return _response(
            content="センサーの急変を検知しました。いたずらの可能性があります。",
            tool_calls=[
                _make_tool_call("speak", {
                    "message": "おや、センサーの値が急に変わりましたね。何かいたずらしてません？",
                    "tone": "humorous",
                })
            ]
        )

    # Person entered -> speak welcome (optional)
    if "person_entered" in full_text or "入室" in full_text:
        return _response(
            content="入室を検知しました。挨拶します。",
            tool_calls=[
                _make_tool_call("speak", {
                    "message": "こんにちは！今日もお疲れさまです。快適な環境を整えておきますね。",
                    "tone": "neutral",
                })
            ]
        )

    # Normal status - no tool calls
    return _response(content="現在のオフィス環境は正常範囲内です。特に対応の必要はありません。")


def _response(content: str, tool_calls: list = None) -> dict:
    """Build OpenAI-compatible chat completion response."""
    message = {"role": "assistant", "content": content}

    if tool_calls:
        message["tool_calls"] = tool_calls
        finish_reason = "tool_calls"
    else:
        finish_reason = "stop"

    return {
        "id": f"mock-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "mock-qwen",
        "choices": [{
            "index": 0,
            "message": message,
            "finish_reason": finish_reason,
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 10,
            "total_tokens": 20,
        }
    }
