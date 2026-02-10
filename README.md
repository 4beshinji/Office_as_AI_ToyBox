# Symbiotic Office Management System (SOMS)

## Overview
SOMS is an autonomous, event-driven office management system that combines Large Language Models (LLM) with IoT to create a comfortable, energy-efficient, and "symbiotic" environment for humans and machines.

## Architecture
-   **Central Intelligence**: LLM (Qwen2.5) acting as the decision maker.
-   **Communication**: MQTT-based Model Context Protocol (MCP).
-   **Perception**: Distributed Vision (YOLOv11) and Sensor Network.
-   **Edge**: ESP32 Microcontrollers for physical interaction (Office, Hydroponics, Aquarium).
-   **Economy**: Honor-based "Office Credit" system to incentivize human tasks.

## Directory Structure
-   `docs/`: Design documentation.
-   `infra/`: Docker Compose and infrastructure config.
-   `services/`: Microservices (Brain, Perception, Dashboard).
-   `edge/`: Firmware for ESP32 and Raspberry Pi.

## Getting Started
See `infra/README.md` (to be created) for deployment instructions.
