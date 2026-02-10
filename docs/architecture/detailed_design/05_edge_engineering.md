# 05. Edge Engineering (ESP32 & Raspberry Pi)

## 1. Overview
The Edge Layer consists of distributed microcontrollers (ESP32) and single-board computers (Raspberry Pi). They act as the "hands and eyes" of the system, bridging the digital commands from the LLM to the physical world.

## 2. ESP32 Cluster: The "Thin Client" Agents
We utilize standard ESP32-WROOM-32 or ESP32-CAM modules.

### 2.1 Firmware Design (MicroPython)
To maintain agility, we use **MicroPython**. The firmware is designed as a generic "MCP Execution Engine" rather than hardcoding logic.

#### Architecture:
1.  **Boot**: Connect Wi-Fi -> Connect MQTT Broker -> Subscribe `mcp/{my_id}/request/#`.
2.  **Loop**: Sleep until message received (Interrupt-driven or yielding wait).
3.  **Parsers**:
    -   `set_gpio(pin, value)`: Generic digital I/O.
    -   `read_sensor(type, pin)`: Generic sensor read (DHT22, BH1750).
    -   `set_pwm(pin, duty)`: Generic analog output (LED dimming).
4.  **Error Handling**: Watchdog Timer (WDT) resets device on freeze.

#### Example "Tool" Implementation (Python on ESP32):
```python
# tool: set_light
def set_light(params):
    pin = int(params.get('pin', 2))
    val = int(params.get('value', 0)) # 0 or 1
    Pin(pin, Pin.OUT).value(val)
    return {"status": "success", "pin": pin, "value": val}
```

### 2.2 Sensor & Actuator Catalog
-   **Environmental**: DHT22/SHT3x (Temp/Hum), BMP280 (Pressure).
-   **Occupancy**: HC-SR501 (PIR Motion), LD2410 (mmWave Radar - more accurate than PIR).
-   **Visual**: OV2640 (ESP32-CAM) for low-res snapshots.
-   **Actuation**: Relay Modules (Lights/Fans), IR Transmitters (Legacy AC control).

## 3. Raspberry Pi Cluster: Edge AI & Gateway
Raspberry Pi 4 (4GB+) or Pi 5 serves as a **Local Gateway** and **Vision Server**.

### 3.1 Role 1: Camera Server (RTSP)
-   Handles USB Webcams or CSI Cameras.
-   Runs `mediamtx` or similar robust RTSP server to stream video to the Central GPU Server.
-   *Resilience*: If Central Server goes down, Pi can store local recordings (Loop recording).

### 3.2 Role 2: Fallback Logic
If the Central Intelligence (LLM) is unreachable (Network/Server failure), the Pi takes over critical logic.
-   **Watchdog**: Pings Central Server every 10s.
-   **Safe Mode**: If ping fails -> Switch to `SAFE_MODE`.
    -   Basic rules: "If Temp > 28C, Turn on Fan".
    -   Run lightweight **YOLOv8-Nano** locally for basic intruder detection.

## 4. Hardware Deployment Strategy
### 4.1 Zone-Based Hubs
Instead of wiring everything to a central closet, we use "Zone Hubs".
-   **Hub A (Meeting Room)**: 1x Pi 4 + 3x ESP32.
-   **Hub B (Kitchen)**: 1x Pi Zero 2W + 2x ESP32.

### 4.2 Power & Connectivity
-   **Power**: PoE (Power over Ethernet) splitters for Pis, USB adapters for ESP32s.
-   **Network**: Dedicated 2.4GHz Wi-Fi SSID (`SOMS_IoT_VLAN`) isolated from corporate LAN for security.

## 5. Water Management Module (Hydroponics & Aquarium)
To support the office's biophilic elements, a dedicated high-reliability controller ensures optimal water quality.

### 5.1 Hardware Stack
-   **Controller**: ESP32 with Relay Board (8-channel) and Analog Extender (ADS1115) for high-precision sensors.
-   **Sensors**:
    -   **DS18B20**: Water Temperature (Waterproof).
    -   **Analog pH Sensor**: industrial grade probe.
    -   **Analog TDS/EC Sensor**: Total Dissolved Solids / Electrical Conductivity (Nutrient strength).
    -   **Non-contact Liquid Level Sensor**: XKC-Y25 attached to tank exterior.
-   **Actuators**:
    -   **Peristaltic Pumps**: Precise dosing of Liquid Fertilizer (A/B solutions) and pH Down/Up.
    -   **Air Pump**: Oxygenation (Always ON / Intermittent).
    -   **Circulation Pump**: Water movement.
    -   **Heater/Chiller**: Temperature control (via Relay).

### 5.2 Automation Logic (Edge Side)
While the LLM can oversee trends, the feedback loop for dosing must be local to prevent over-dosing due to network latency.
-   **Rule**: `IF pH > 7.0 THEN Pump_pH_Down(5ml) WAIT 15min`.
-   **Safety**: Max dosing limit per day (Hardcoded).

### 5.3 Human Interaction
-   **Manual Tasks**: "Water change", "Harvesting", "Refilling Nutrient Reservoirs" are delegated to humans via the Task Board.
-   **Emergency**: "Leak detected" triggers immediate pump shutdown and "High Urgency" notification.
