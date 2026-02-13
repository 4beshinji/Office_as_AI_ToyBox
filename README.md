# Symbiotic Office Management System (SOMS)

LLM "Brain" + IoT + Computer Vision による自律オフィス管理システム。
センサーデータとカメラ映像をもとに LLM がリアルタイムで環境制御（照明・空調）やタスク委任を判断し、クレジット経済で人間との協調を実現します。

## Architecture

```
                ┌──────────────────┐
                │   Ollama / LLM   │
                │  (qwen2.5:14b)   │
                └────────┬─────────┘
                         │ OpenAI API
                ┌────────┴─────────┐
                │   Brain Service   │
                │  ReAct Loop (5x)  │
                │  WorldModel       │
                │  TaskScheduling   │
                └──┬───┬───┬───┬───┘
                   │   │   │   │
        ┌──────────┘   │   │   └──────────┐
        ▼              ▼   ▼              ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│ MQTT Broker  │ │  Dashboard  │ │Voice Service │
│ (Mosquitto)  │ │  Backend    │ │  + VOICEVOX  │
└──┬───┬───────┘ │  (FastAPI)  │ └──────────────┘
   │   │         └──────┬──────┘
   │   │                │
   │   │         ┌──────┴──────┐
   │   │         │  Dashboard  │
   │   │         │  Frontend   │◄── nginx ──► Wallet
   │   │         │  (React 19) │              Service
   │   │         └─────────────┘
   │   │
   │   └─────────────────┐
   ▼                     ▼
┌──────────────┐  ┌──────────────┐
│ Edge Devices │  │  Perception  │
│ SwarmHub +   │  │  YOLOv11     │
│ Leaf nodes   │  │  Monitors    │
│ MCP/JSON-RPC │  │  (ROCm GPU)  │
└──────────────┘  └──────────────┘
```

### Layers

| Layer | Directory | Description |
|-------|-----------|-------------|
| Central Intelligence | `services/brain/` | LLM-driven ReAct cognitive loop (Think→Act→Observe) |
| Perception | `services/perception/` | YOLOv11 vision — occupancy, whiteboard, activity monitors |
| Communication | MQTT (Mosquitto) | MCP over MQTT with JSON-RPC 2.0 payloads |
| Edge | `edge/` | ESP32 sensors/relays + SensorSwarm Hub-Leaf 2-tier network |
| Human Interface | `services/dashboard/`, `services/voice/` | React 19 dashboard + VOICEVOX voice synthesis |
| Economy | `services/wallet/` | Double-entry credit ledger with device XP |

## Services

| Service | Port | Container |
|---------|------|-----------|
| Dashboard Frontend (nginx) | 80 | soms-frontend |
| Dashboard Backend API | 8000 | soms-backend |
| Mock LLM | 8001 | soms-mock-llm |
| Voice Service | 8002 | soms-voice |
| Wallet Service | 8003 | soms-wallet |
| PostgreSQL | 5432 | soms-postgres |
| VOICEVOX Engine | 50021 | soms-voicevox |
| Ollama (LLM) | 11434 | soms-ollama |
| MQTT Broker | 1883 | soms-mqtt |

## Quick Start

```bash
# 1. Clone and configure
git clone <repository_url>
cd Office_as_AI_ToyBox
cp env.example .env

# 2. Full simulation (no GPU/hardware required)
./infra/scripts/start_virtual_edge.sh

# 3. Production (AMD ROCm GPU + real hardware)
docker compose -f infra/docker-compose.yml up -d --build
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed setup instructions.

## Directory Structure

```
├── docs/              Design documentation
├── infra/             Docker Compose, Mosquitto, mock LLM, virtual edge/camera
├── services/
│   ├── brain/         LLM decision engine (ReAct loop, WorldModel, task scheduling)
│   ├── dashboard/     Frontend (React 19 + Vite) + Backend (FastAPI)
│   ├── perception/    YOLOv11 vision system (pluggable monitors)
│   ├── voice/         VOICEVOX voice synthesis + LLM text generation
│   └── wallet/        Double-entry credit ledger + device XP
├── edge/
│   ├── office/        Production MicroPython firmware (BME680, MH-Z19C)
│   ├── swarm/         SensorSwarm Hub + Leaf firmware (ESP-NOW, UART, I2C)
│   ├── lib/           Shared libraries (soms_mcp.py, swarm protocol)
│   ├── test-edge/     PlatformIO C++ firmware (camera/sensor nodes)
│   └── tools/         Diagnostic scripts
├── config/            Perception monitors YAML config
├── CLAUDE.md          Developer reference (architecture, APIs, conventions)
└── DEPLOYMENT.md      Deployment guide (Japanese)
```

## Tech Stack

- **LLM**: Ollama + Qwen2.5:14b (ROCm, AMD GPU)
- **Backend**: Python 3.11, FastAPI, SQLAlchemy (async), PostgreSQL / SQLite
- **Frontend**: React 19, TypeScript, Vite 7, Tailwind CSS 4, Framer Motion
- **Vision**: YOLOv11 (yolo11s.pt + yolo11s-pose.pt), OpenCV, PyTorch (ROCm)
- **TTS**: VOICEVOX (Japanese, Speaker ID 47: ナースロボ_タイプT)
- **Edge**: MicroPython (ESP32/Pico) + PlatformIO C++ (ATtiny/ESP32-CAM)
- **Infra**: Docker Compose, Mosquitto MQTT, nginx

## Testing

```bash
# E2E integration test (7 scenarios)
python3 infra/scripts/e2e_full_test.py

# Individual tests
python3 infra/scripts/integration_test_mock.py
python3 infra/scripts/test_task_scheduling.py
python3 infra/scripts/test_world_model.py
```

## License

See LICENSE file.
