# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SOMS (Symbiotic Office Management System)** — an autonomous, event-driven office management system combining an LLM "brain" with IoT edge devices, computer vision, and a credit-based economy for human-AI collaboration. The LLM makes real-time decisions about the office environment (lighting, HVAC, task delegation) using sensor data and camera feeds.

## Build & Run Commands

All services run via Docker Compose from the `infra/` directory.

```bash
# Initial setup (create volumes, build containers)
cp env.example .env
./infra/scripts/setup_dev.sh

# Full simulation (no GPU/hardware required) — uses mock LLM + virtual edge devices
./infra/scripts/start_virtual_edge.sh

# Production (requires AMD ROCm GPU + real hardware)
docker compose -f infra/docker-compose.yml up -d --build

# Rebuild a single service
docker compose -f infra/docker-compose.yml up -d --build <service-name>

# View logs
docker logs -f soms-brain
docker logs -f soms-perception
```

Service names in docker-compose: `mosquitto`, `brain`, `backend`, `frontend`, `voicevox`, `voice-service`, `ollama`, `mock-llm`, `perception`

### Testing

Tests are standalone Python scripts (no pytest framework):

```bash
# Integration test (end-to-end with mock LLM)
python3 infra/scripts/integration_test_mock.py

# Individual test scripts
python3 infra/scripts/test_task_scheduling.py
python3 infra/scripts/test_world_model.py
python3 infra/scripts/test_human_task.py
```

Perception service has test scripts in `services/perception/`:
```bash
python3 services/perception/test_activity.py
python3 services/perception/test_discovery.py
python3 services/perception/test_yolo_detect.py
```

## Architecture

### 4-Layer Design

1. **Central Intelligence** (`services/brain/`) — LLM-driven decision engine using a ReAct (Think→Act→Observe) cognitive loop. Cycles every 30s or on new MQTT events, max 5 iterations per cycle.
2. **Perception** (`services/perception/`) — YOLOv11 vision system with configurable monitors (occupancy, whiteboard, activity) defined in `config/monitors.yaml`. Uses host networking for camera access.
3. **Communication** — MQTT broker (Mosquitto) as central message bus. Uses MCP (Model Context Protocol) over MQTT with JSON-RPC 2.0 payloads. Topics: `mcp/{agent_id}/request/{method}` and `mcp/{agent_id}/response/{request_id}`.
4. **Edge** (`edge/`) — ESP32 MicroPython firmware for sensors (BME680, MH-Z19 CO2) and relays. Thin-client design: logic lives on central server.

### Service Ports

| Service | Port | Notes |
|---------|------|-------|
| Dashboard Frontend | 80 | React + nginx |
| Dashboard Backend API | 8000 | FastAPI, Swagger at `/docs` |
| Mock LLM | 8001 | Keyword-based simulator for dev |
| Voice Service | 8002 | TTS via VOICEVOX |
| VOICEVOX Engine | 50021 | Speech synthesis backend |
| Ollama (LLM) | 11434 | ROCm GPU, OpenAI-compatible API |
| MQTT | 1883 | Mosquitto broker |

### Inter-Service Communication

- **Brain ↔ Edge Devices**: MCP over MQTT (JSON-RPC 2.0)
- **Brain → Dashboard**: REST API (`POST/GET/PUT /tasks`)
- **Brain → Voice**: REST API (`POST /api/voice/announce`)
- **Perception → MQTT**: Publishes detection state to broker
- **Brain ← MQTT**: Subscribes to sensor telemetry and perception events, triggers cognitive cycles on state changes

### Brain Service Internals (`services/brain/src/`)

- `main.py` — ReAct cognitive loop, MQTT event handler
- `llm_client.py` — vLLM/Ollama API wrapper (OpenAI-compatible)
- `mcp_bridge.py` — MQTT ↔ JSON-RPC translation layer
- `world_model/` — Sensor fusion, zone/device state tracking
- `task_scheduling/` — Priority queue for LLM-generated tasks
- `tool_registry.py` — Tool definitions for LLM function calling
- `tool_executor.py` — Executes tool calls from LLM responses
- `system_prompt.py` — Constitutional AI system prompt builder
- `sanitizer.py` — Input validation and security

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy (async), paho-mqtt >=2.0, Pydantic 2.x, loguru
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS 4, Framer Motion
- **ML/Vision**: Ultralytics YOLOv11, OpenCV, PyTorch (ROCm)
- **LLM**: Ollama with ROCm for AMD GPUs (Qwen2.5-32B target model)
- **Edge**: MicroPython on ESP32, PlatformIO C++ for camera/sensor nodes
- **Infra**: Docker Compose, Mosquitto MQTT, SQLite (aiosqlite)

## Code Conventions

- All Python I/O uses `async/await` (asyncio event loop)
- Configuration via environment variables (`.env` file, `python-dotenv`)
- LLM tools follow OpenAI function-calling schema with explicit `parameters.properties` and `required` fields
- Source code is bind-mounted into containers (`volumes: - ../services/X/src:/app`), so changes take effect on container restart without rebuild
- Documentation is bilingual (English code/comments, Japanese deployment docs)
- Perception monitors are YAML-configured (`services/perception/config/monitors.yaml`), not hardcoded

## Environment Configuration

Key variables in `.env` (see `env.example`):

- `LLM_API_URL` — `http://mock-llm:8000/v1` (dev) or `http://ollama:11434/v1` (prod)
- `LLM_MODEL` — Model name for Ollama
- `MQTT_BROKER` / `MQTT_PORT` — Broker address (default: `mosquitto:1883`)
- `DATABASE_URL` — SQLite path for dashboard
- `RTSP_URL` — Camera feed URL
- `TZ` — Timezone (default: `Asia/Tokyo`)
