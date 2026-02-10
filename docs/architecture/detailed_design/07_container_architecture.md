# 07. Containerization & Orchestration

## 1. Portable Infrastructure Strategy
To ensure the system is hardware-agnostic and easy to deploy/migrate, we adopt a **Container-Native** architecture using Docker and Docker Compose. This encapsulates dependencies (CUDA/ROCm drivers, Python libraries, System tools) into reproducible images.

## 2. Container Service Architecture
The system is composed of the following microservices defined in a single `docker-compose.yml`.

| Service Name | Base Image | Role | Resources |
| :--- | :--- | :--- | :--- |
| `mosquitto` | `eclipse-mosquitto:latest` | MQTT Broker (Central Nervous System) | Low |
| `llm-engine` | `rocm/vllm:latest` (Custom Build) | LLM Inference API | **GPU (32GB VRAM)** |
| `perception` | `pytorch/pytorch:rocm` | YOLOv11 Vision Analysis | Shared GPU / CPU |
| `brain-bridge` | `python:3.11-slim` | Main Event Loop & MCP Logic | CPU |
| `backend` | `python:3.11-slim` | FastAPI Dashboard API | CPU |
| `frontend` | `nginx:alpine` | React SPA static host | Low |

## 3. GPU Passthrough (AMD Radeon)
For the `llm-engine` to access the AMD Radeon GPU, we must map the devices into the container.

### `docker-compose.yml` Fragment
```yaml
services:
  llm-engine:
    image: soms/vllm-rocm:latest
    devices:
      - /dev/kfd  # AMD Kernel Fusion Driver
      - /dev/dri  # Direct Rendering Infrastructure
    group_add:
      - video
    security_opt:
      - seccomp:unconfined
    volumes:
      - ./models:/root/.cache/huggingface
    environment:
      - HUGGING_FACE_HUB_TOKEN=${HF_TOKEN}
```

## 4. Volume Strategy (Persistence)
To ensure portability, all state must be stored in named volumes or bind mounts, never inside the container layer.
-   **`soms_db_data`**: Mapped to `backend` for SQLite file storage (`/data/soms.db`).
-   **`soms_models`**: Mapped to `llm-engine` and `perception` to avoid re-downloading large weights (`/models`).
-   **`soms_logs`**: Shared volume for centralized logging.

## 5. Network Topology (Distributed Ready)
-   **Internal Network (`soms-net`)**: Backend, Brain, LLM, and Perception communicate here.
-   **Host Exposure**:
    -   `mosquitto`: Port 1883 (Binding to `0.0.0.0` allows external nodes to connect).
    -   `frontend`: Port 80 (Dashboard access).
    -   `backend`: Port 8000 (API Access for remote scripts).
    -   `perception`: Port 8554 (RTSP Stream for remote viewing).

## 6. Build & Deployment Workflow
1.  **Development**: Developers work with `dev.Dockerfile` which mounts the `/src` directory for live-reloading.
2.  **Production**: `prod.Dockerfile` copies source code and pre-compiles assets.
3.  **Migration**: To move to a new machine:
    1.  Copy `docker-compose.yml` and `.env` (Secrets).
    2.  Rsync the `./volumes/` folder (Database, Models).
    3.  Run `docker compose up -d`.

## 7. Extensions for Edge
Specific Docker profiles (e.g., `docker-compose.edge.yaml`) can be created for Raspberry Pi nodes, excluding the heavy `llm-engine` but keeping `perception` (Nano model) and `mosquitto` (Bridge mode).
